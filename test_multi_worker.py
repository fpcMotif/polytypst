import torch, multiprocessing as mp, time
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
from pathlib import Path

def worker(worker_id, page_paths, return_dict):
    print(f"[Worker {worker_id}] Loading model on GPU...")
    t0 = time.time()
    processor = AutoProcessor.from_pretrained("jinaai/jina-ocr-v1", trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        "jinaai/jina-ocr-v1",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    ).to("cuda").eval()
    
    t_start = time.time()
    for p_path in page_paths:
        img = Image.open(p_path).convert("RGB")
        inp = processor.prepare_ocr_inputs(img, device="cuda")
        with torch.inference_mode():
            out = model.generate(**inp, max_new_tokens=4096, do_sample=False)
        txt = processor.decode_ocr(out, inp["input_ids"])[0]
    duration = time.time() - t_start
    return_dict[worker_id] = duration
    print(f"[Worker {worker_id}] Finished {len(page_paths)} pages in {duration:.2f}s ({duration/len(page_paths):.2f}s/page)")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    pages = list(Path("/content/pages").glob("*.png"))[:4]
    half = len(pages) // 2
    w1_pages, w2_pages = pages[:half], pages[half:]
    
    manager = mp.Manager()
    ret = manager.dict()
    
    t_all_start = time.time()
    p1 = mp.Process(target=worker, args=(1, w1_pages, ret))
    p2 = mp.Process(target=worker, args=(2, w2_pages, ret))
    p1.start(); p2.start()
    p1.join(); p2.join()
    t_all = time.time() - t_all_start
    print(f"\nTOTAL PARALLEL TIME: {t_all:.2f}s for {len(pages)} pages!")
    print(f"Effective throughput: {len(pages)/t_all:.2f} pages/s ({t_all/len(pages):.2f}s/page)")
