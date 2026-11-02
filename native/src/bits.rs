use numpy::ndarray::{Array2, ArrayView2};
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2};
use pyo3::prelude::*;

use crate::index_runs;

const GATHER_BYTE_BITS: u64 = 0x0102_0408_1020_4080;

pub type Block = (usize, usize, usize, usize, usize);
pub type InkDiff = (usize, usize, usize, usize, Vec<Block>, Vec<Block>);
type Grid<'py> = Bound<'py, PyArray2<bool>>;

struct Bits {
    h: usize,
    words: usize,
    data: Vec<u64>,
}

fn pack_byte_bits(bytes: &[bool]) -> u64 {
    let mut b = [0u8; 8];
    for (d, &s) in b.iter_mut().zip(bytes) {
        *d = u8::from(s);
    }
    u64::from_le_bytes(b).wrapping_mul(GATHER_BYTE_BITS) >> 56
}

fn range_mask(word: usize, x0: usize, x1: usize) -> u64 {
    let lo = x0.saturating_sub(word * 64).min(64);
    let hi = (x1 + 1).saturating_sub(word * 64).min(64);
    let upto = |n: usize| if n == 64 { u64::MAX } else { (1u64 << n) - 1 };
    upto(hi) & !upto(lo)
}

impl Bits {
    fn pack(ink: &ArrayView2<'_, bool>, h: usize, w: usize) -> Bits {
        let words = w.div_ceil(64);
        let mut data = vec![0u64; h * words];
        for (y, out) in data.chunks_mut(words.max(1)).enumerate().take(h) {
            let row = ink.row(y);
            match row.as_slice() {
                Some(row) => {
                    for (word, chunk) in out.iter_mut().zip(row[..w].chunks(64)) {
                        *word = chunk.chunks(8).enumerate().fold(0, |acc, (k, b)| acc | pack_byte_bits(b) << (8 * k));
                    }
                }
                None => {
                    for (x, &v) in row.iter().take(w).enumerate() {
                        out[x / 64] |= u64::from(v) << (x % 64);
                    }
                }
            }
        }
        Bits { h, words, data }
    }

    fn row(&self, y: usize) -> &[u64] {
        &self.data[y * self.words..(y + 1) * self.words]
    }

    fn count(&self) -> usize {
        self.data.iter().map(|v| v.count_ones() as usize).sum()
    }

    fn range_count(&self, y: usize, x0: usize, x1: usize) -> usize {
        let row = self.row(y);
        (x0 / 64..=x1 / 64).map(|i| (row[i] & range_mask(i, x0, x1)).count_ones() as usize).sum()
    }

    fn grown_by_one(&self) -> Bits {
        let n = self.words;
        let mut data = vec![0u64; self.data.len()];
        for (out, src) in data.chunks_mut(n.max(1)).zip(self.data.chunks(n.max(1))) {
            for i in 0..n {
                let up = src[i] << 1 | if i > 0 { src[i - 1] >> 63 } else { 0 };
                let down = src[i] >> 1 | if i + 1 < n { src[i + 1] << 63 } else { 0 };
                out[i] = src[i] | up | down;
            }
        }
        Bits { h: self.h, words: n, data }
    }

    fn within_manhattan(&self, radius: usize) -> Bits {
        let mut grown = vec![Bits { h: self.h, words: self.words, data: self.data.clone() }];
        for k in 0..radius {
            grown.push(grown[k].grown_by_one());
        }
        let mut data = vec![0u64; self.data.len()];
        for y in 0..self.h {
            let out = &mut data[y * self.words..(y + 1) * self.words];
            for yy in y.saturating_sub(radius)..=(y + radius).min(self.h - 1) {
                for (o, &v) in out.iter_mut().zip(grown[radius - yy.abs_diff(y)].row(yy)) {
                    *o |= v;
                }
            }
        }
        Bits { h: self.h, words: self.words, data }
    }

    fn and_not(&self, other: &Bits) -> Bits {
        let data = self.data.iter().zip(&other.data).map(|(a, b)| a & !b).collect();
        Bits { h: self.h, words: self.words, data }
    }

    fn set_columns(cols: &[u64]) -> impl Iterator<Item = usize> + '_ {
        cols.iter().enumerate().flat_map(|(i, &word)| {
            std::iter::successors((word != 0).then_some(word), |&v| Some(v & (v - 1)).filter(|&v| v != 0))
                .map(move |v| i * 64 + v.trailing_zeros() as usize)
        })
    }

    fn band_blocks(&self, gap_y: usize, gap_x: usize) -> Vec<Block> {
        let inked = (0..self.h).filter(|&y| self.row(y).iter().any(|&v| v != 0));
        let mut out = Vec::new();
        for (y0, y1) in index_runs(inked, gap_y) {
            let mut cols = vec![0u64; self.words];
            for y in y0..=y1 {
                for (c, &v) in cols.iter_mut().zip(self.row(y)) {
                    *c |= v;
                }
            }
            for (x0, x1) in index_runs(Bits::set_columns(&cols), gap_x) {
                let (mut n, mut top, mut bottom) = (0, usize::MAX, 0);
                for y in y0..=y1 {
                    let k = self.range_count(y, x0, x1);
                    if k > 0 {
                        n += k;
                        top = top.min(y);
                        bottom = y;
                    }
                }
                out.push((x0, top, x1 + 1, bottom + 1, n));
            }
        }
        out
    }

    fn inked_cells(&self, w: usize, cell: usize, min_share: f64) -> Array2<bool> {
        let (gh, gw) = (self.h / cell, w / cell);
        let area = (cell * cell) as f64;
        let mut out = Array2::from_elem((gh, gw), false);
        for ((gy, gx), o) in out.indexed_iter_mut() {
            let n: usize =
                (gy * cell..(gy + 1) * cell).map(|y| self.range_count(y, gx * cell, (gx + 1) * cell - 1)).sum();
            *o = n as f64 / area >= min_share;
        }
        out
    }
}

#[pyclass(frozen)]
pub struct InkPair {
    source: Bits,
    rebuilt: Bits,
    #[pyo3(get)]
    width: usize,
}

#[pymethods]
impl InkPair {
    #[new]
    fn new(py: Python<'_>, source: PyReadonlyArray2<'_, bool>, rebuilt: PyReadonlyArray2<'_, bool>) -> Self {
        let (a, b) = (source.as_array(), rebuilt.as_array());
        let (h, width) = (a.nrows().min(b.nrows()), a.ncols().min(b.ncols()));
        py.detach(|| InkPair { source: Bits::pack(&a, h, width), rebuilt: Bits::pack(&b, h, width), width })
    }

    fn diff(&self, py: Python<'_>, radius: usize, gap_y: usize, gap_x: usize) -> InkDiff {
        py.detach(|| {
            if self.source.h == 0 || self.width == 0 {
                return (0, 0, 0, 0, Vec::new(), Vec::new());
            }
            let extra = self.rebuilt.and_not(&self.source.within_manhattan(radius));
            let missing = self.source.and_not(&self.rebuilt.within_manhattan(radius));
            (
                self.source.count(),
                self.rebuilt.count(),
                extra.count(),
                missing.count(),
                extra.band_blocks(gap_y, gap_x),
                missing.band_blocks(gap_y, gap_x),
            )
        })
    }

    fn inked_cells<'py>(&self, py: Python<'py>, cell: usize, min_share: f64) -> (Grid<'py>, Grid<'py>) {
        let (a, b) = py.detach(|| {
            (
                self.source.inked_cells(self.width, cell, min_share),
                self.rebuilt.inked_cells(self.width, cell, min_share),
            )
        });
        (a.into_pyarray(py), b.into_pyarray(py))
    }
}
