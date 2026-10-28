use std::any::Any;
use std::collections::HashMap;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};

use comemo::Track;
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use termcolor::NoColor;
use typst::diag::{FileResult, SourceDiagnostic, Warned};
use typst::engine::Sink;
use typst::foundations::{Bytes, Context, Datetime, Dict, Duration, IntoValue, LocatableSelector, Scope, Smart};
use typst::introspection::{EmptyIntrospector, Introspector};
use typst::routines::SpanMode;
use typst::syntax::{FileId, RootedPath, Source, Span, SyntaxMode, VirtualPath, VirtualRoot};
use typst::text::{Font, FontBook};
use typst::utils::LazyHash;
use typst::{Library, LibraryExt, World};
use typst_kit::datetime::Time;
use typst_kit::diagnostics::{self, DiagnosticFormat, DiagnosticWorld};
use typst_kit::downloader::Downloader;
use typst_kit::files::{FileLoader, FileStore, FsRoot};
use typst_kit::fonts::{self, FontStore};
use typst_kit::packages::{FsPackages, SystemPackages, UniversePackages};
use typst_layout::PagedDocument;
use typst_pdf::{PdfOptions, PdfStandards};
use typst_render::RenderOptions;

pyo3::create_exception!(polytypst_native, TypstError, PyRuntimeError);

const MAX_DOCS: usize = 64;
const STACK_BYTES: usize = 1 << 30;

fn on_big_stack<T: Send>(run: impl FnOnce() -> Result<T, String> + Send) -> Result<T, String> {
    std::thread::scope(|scope| {
        let worker = std::thread::Builder::new()
            .stack_size(STACK_BYTES)
            .spawn_scoped(scope, run)
            .map_err(|e| format!("cannot start the typst thread ({e})"))?;
        worker.join().unwrap_or_else(|panic| {
            let message = panic
                .downcast_ref::<String>()
                .map(String::as_str)
                .or_else(|| panic.downcast_ref::<&str>().copied())
                .unwrap_or("unknown panic");
            Err(format!("typst panicked: {message}"))
        })
    })
}

struct Offline;

impl Downloader for Offline {
    fn stream(&self, _key: &dyn Any, url: &str) -> io::Result<(Option<usize>, Box<dyn io::Read>)> {
        Err(io::Error::other(format!("offline: package not in the local cache ({url})")))
    }
}

struct Files {
    main: FileId,
    project: FsRoot,
    packages: SystemPackages,
}

impl FileLoader for Files {
    fn load(&self, id: FileId) -> FileResult<Bytes> {
        let root = match id.root() {
            VirtualRoot::Project => self.project.clone(),
            VirtualRoot::Package(spec) => self.packages.obtain(spec)?,
        };
        root.load(id.vpath())
    }
}

struct Doc {
    library: LazyHash<Library>,
    inputs: Vec<(String, String)>,
    fonts: Arc<FontStore>,
    files: FileStore<Files>,
    now: Time,
}

impl World for Doc {
    fn library(&self) -> &LazyHash<Library> {
        &self.library
    }
    fn book(&self) -> &LazyHash<FontBook> {
        self.fonts.book()
    }
    fn main(&self) -> FileId {
        self.files.loader().main
    }
    fn source(&self, id: FileId) -> FileResult<Source> {
        self.files.source(id)
    }
    fn file(&self, id: FileId) -> FileResult<Bytes> {
        self.files.file(id)
    }
    fn font(&self, index: usize) -> Option<Font> {
        self.fonts.font(index)
    }
    fn today(&self, offset: Option<Duration>) -> Option<Datetime> {
        self.now.today(offset)
    }
}

impl DiagnosticWorld for Doc {
    fn name(&self, id: FileId) -> String {
        match id.root() {
            VirtualRoot::Project => id
                .vpath()
                .realize(self.files.loader().project.path())
                .map(|path| path.to_string_lossy().into_owned())
                .unwrap_or_else(|_| id.vpath().get_without_slash().into()),
            VirtualRoot::Package(spec) => format!("{spec}{}", id.vpath().get_with_slash()),
        }
    }
}

fn library(inputs: &[(String, String)]) -> LazyHash<Library> {
    let dict: Dict = inputs.iter().map(|(k, v)| (k.as_str().into(), v.as_str().into_value())).collect();
    LazyHash::new(Library::builder().with_inputs(dict).build())
}

fn report(world: &Doc, diags: &[SourceDiagnostic]) -> String {
    let mut out = NoColor::new(Vec::new());
    let _ = diagnostics::emit(&mut out, world, diags, DiagnosticFormat::Short);
    String::from_utf8_lossy(&out.into_inner()).into_owned()
}

#[pyclass(frozen)]
pub struct Typst {
    fonts: Arc<FontStore>,
    docs: Mutex<HashMap<(PathBuf, PathBuf), Doc>>,
}

impl Typst {
    fn with_doc<T>(
        &self,
        main: &Path,
        root: Option<&Path>,
        inputs: HashMap<String, String>,
        run: impl FnOnce(&Doc) -> Result<T, String>,
    ) -> Result<T, String> {
        let main = main.canonicalize().map_err(|e| format!("input file not found: {} ({e})", main.display()))?;
        let root = root
            .unwrap_or_else(|| main.parent().unwrap_or(Path::new(".")))
            .canonicalize()
            .map_err(|e| format!("root directory not found ({e})"))?;
        let mut inputs: Vec<(String, String)> = inputs.into_iter().collect();
        inputs.sort();
        let mut docs = self.docs.lock().map_err(|_| "typst world lock poisoned".to_string())?;
        if docs.len() >= MAX_DOCS && !docs.contains_key(&(main.clone(), root.clone())) {
            docs.clear();
        }
        let doc = match docs.entry((main.clone(), root.clone())) {
            std::collections::hash_map::Entry::Occupied(e) => e.into_mut(),
            std::collections::hash_map::Entry::Vacant(e) => {
                let vpath = VirtualPath::virtualize(&root, &main).map_err(|_| "source file must be inside the root".to_string())?;
                let packages = SystemPackages::from_parts(
                    FsPackages::system_data(),
                    FsPackages::system_cache(),
                    UniversePackages::new(Offline),
                );
                e.insert(Doc {
                    library: library(&inputs),
                    inputs: inputs.clone(),
                    fonts: self.fonts.clone(),
                    files: FileStore::new(Files {
                        main: RootedPath::new(VirtualRoot::Project, vpath).intern(),
                        project: FsRoot::new(root),
                        packages,
                    }),
                    now: Time::system(),
                })
            }
        };
        if doc.inputs != inputs {
            doc.library = library(&inputs);
            doc.inputs = inputs;
        }
        doc.files.reset();
        doc.now.reset();
        let result = run(doc);
        comemo::evict(10);
        result
    }

    fn compile_doc(doc: &Doc) -> Result<(PagedDocument, String), String> {
        let Warned { output, warnings } = typst::compile::<PagedDocument>(doc);
        let warned = report(doc, &warnings);
        output.map(|d| (d, warned.clone())).map_err(|errors| report(doc, &errors) + &warned)
    }
}

#[pymethods]
impl Typst {
    #[new]
    fn new(font_paths: Vec<PathBuf>) -> Self {
        let mut store = FontStore::new();
        store.extend(fonts::system());
        store.extend(fonts::embedded());
        for path in &font_paths {
            store.extend(fonts::scan(path));
        }
        Typst { fonts: Arc::new(store), docs: Mutex::new(HashMap::new()) }
    }

    #[pyo3(signature = (main, root=None, inputs=HashMap::new(), format="pdf", ppi=144.0, pdf_tags=true))]
    fn compile(
        &self,
        py: Python<'_>,
        main: PathBuf,
        root: Option<PathBuf>,
        inputs: HashMap<String, String>,
        format: &str,
        ppi: f64,
        pdf_tags: bool,
    ) -> PyResult<(Option<Py<PyBytes>>, String)> {
        let format = format.to_owned();
        let out = py.detach(|| on_big_stack(|| {
            self.with_doc(&main, root.as_deref(), inputs, |doc| {
                let (document, warnings) = Self::compile_doc(doc)?;
                let bytes = match format.as_str() {
                    "pdf" => {
                        let options = PdfOptions {
                            ident: Smart::Auto,
                            creator: Smart::Auto,
                            timestamp: None,
                            page_ranges: None,
                            standards: PdfStandards::default(),
                            tagged: pdf_tags,
                            pretty: false,
                        };
                        Some(typst_pdf::pdf(&document, &options).map_err(|errors| report(doc, &errors))?)
                    }
                    "png" => {
                        let [page] = document.pages() else {
                            return Err(format!("png export needs one page, got {}", document.pages().len()));
                        };
                        let options = RenderOptions { pixel_per_pt: (ppi / 72.0).into(), render_bleed: false };
                        Some(typst_render::render(page, &options).encode_png().map_err(|e| e.to_string())?)
                    }
                    "none" => None,
                    other => return Err(format!("unknown format {other}")),
                };
                Ok((bytes, warnings))
            })
        }));
        let (bytes, warnings) = out.map_err(TypstError::new_err)?;
        Ok((bytes.map(|b| PyBytes::new(py, &b).unbind()), warnings))
    }

    #[pyo3(signature = (main, selector, field=None, root=None, inputs=HashMap::new()))]
    fn query(
        &self,
        py: Python<'_>,
        main: PathBuf,
        selector: String,
        field: Option<String>,
        root: Option<PathBuf>,
        inputs: HashMap<String, String>,
    ) -> PyResult<String> {
        py.detach(|| on_big_stack(|| {
            self.with_doc(&main, root.as_deref(), inputs, |doc| {
                let (document, _) = Self::compile_doc(doc)?;
                let selector = typst_eval::eval_string(
                    (doc as &dyn World).track(),
                    doc.library(),
                    Sink::new().track_mut(),
                    EmptyIntrospector.track(),
                    Context::none().track(),
                    &selector,
                    SpanMode::Uniform(Span::detached()),
                    SyntaxMode::Code,
                    Scope::default(),
                )
                .map_err(|errors| format!("failed to evaluate selector: {}", report(doc, &errors)))?
                .cast::<LocatableSelector>()
                .map_err(|e| e.message().to_string())?;
                let values: Vec<_> = document
                    .introspector()
                    .query(&selector.0)
                    .into_iter()
                    .filter_map(|c| match &field {
                        Some(name) => c.get_by_name(name).ok(),
                        None => Some(c.into_value()),
                    })
                    .collect();
                serde_json::to_string(&values).map_err(|e| e.to_string())
            })
        }))
        .map_err(TypstError::new_err)
    }
}
