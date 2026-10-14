import json, sys
from collections import Counter

QUESTIONS = [  # (id, type, question, gold arXiv ids)
 ("q01","single","Which attention weight matrices does LoRA adapt in its main experiments, and which weights stay frozen?",["2106.09685"]),
 ("q02","single","What is the NF4 data type and why does QLoRA use it?",["2305.14314"]),
 ("q03","single","What is double quantization in QLoRA?",["2305.14314"]),
 ("q04","single","How does DPO's implicit reward relate to the policy and the reference model?",["2305.18290"]),
 ("q05","single","What three-step pipeline does InstructGPT use to align GPT-3 with human intent?",["2203.02155"]),
 ("q06","single","What are the two training phases of Constitutional AI?",["2212.08073"]),
 ("q07","single","How does the IO complexity of FlashAttention compare with standard attention?",["2205.14135"]),
 ("q08","single","What changes does FlashAttention-2 make to work partitioning between thread blocks and warps?",["2307.08691"]),
 ("q09","single","What is the core idea behind GPTQ's one-shot weight quantization?",["2210.17323"]),
 ("q10","single","Why does AWQ protect salient weight channels, and how does it identify them?",["2306.00978"]),
 ("q11","single","How does PagedAttention reduce KV-cache memory fragmentation?",["2309.06180"]),
 ("q12","single","How does speculative decoding preserve the target model's output distribution?",["2211.17192"]),
 ("q13","single","How is a multi-head checkpoint converted into a grouped-query attention model?",["2305.13245"]),
 ("q14","single","How do RAG-Sequence and RAG-Token differ?",["2005.11401"]),
 ("q15","single","How is the DPR dual-encoder trained, and what negatives does it use?",["2004.04906"]),
 ("q16","single","What are reflection tokens in Self-RAG and what do they control?",["2310.11511"]),
 ("q17","single","What is the selection mechanism in Mamba and what problem does it address?",["2312.00752"]),
 ("q18","single","How many experts does Mixtral have per layer, and how many are active per token?",["2401.04088"]),
 ("q19","single","What is Ghost Attention (GAtt) in Llama 2-Chat?",["2307.09288"]),
 ("q20","single","Which attention mechanisms does Mistral 7B use for faster inference and longer sequences?",["2310.06825"]),
 ("q21","definition","What is scaled dot-product attention and why is the dot product scaled?",["1706.03762"]),
 ("q22","definition","What are BERT's two pre-training objectives?",["1810.04805"]),
 ("q23","definition","How does GPT-3 define few-shot in-context learning?",["2005.14165"]),
 ("q24","definition","How does test loss scale with model size, dataset size and compute according to the scaling-laws paper?",["2001.08361"]),
 ("q25","definition","What does compute-optimal mean in Chinchilla, and what model-size to token ratio do the authors find?",["2203.15556"]),
 ("q26","definition","How does rotary position embedding encode absolute position while expressing relative position in attention?",["2104.09864"]),
 ("q27","definition","What is the KV cache and why does it dominate LLM serving memory?",["2309.06180"]),
 ("q28","definition","How is the reward model trained from human comparisons in InstructGPT?",["2203.02155"]),
 ("q29","definition","What is the per-layer complexity of self-attention compared with recurrent and convolutional layers?",["1706.03762"]),
 ("q30","definition","What masking procedure does BERT use for masked language modeling?",["1810.04805"]),
 ("q31","comparison","How do LoRA and QLoRA differ in memory use and base-model precision?",["2106.09685","2305.14314"]),
 ("q32","comparison","How do GPTQ and AWQ differ in their quantization approach?",["2210.17323","2306.00978"]),
 ("q33","comparison","What did FlashAttention-2 improve over the original FlashAttention?",["2205.14135","2307.08691"]),
 ("q34","comparison","How does DPO differ from the RLHF pipeline used in InstructGPT?",["2203.02155","2305.18290"]),
 ("q35","comparison","How does the source of preference labels differ between Constitutional AI and InstructGPT?",["2212.08073","2203.02155"]),
 ("q36","comparison","How does Self-RAG's retrieval decision differ from the original RAG model's?",["2005.11401","2310.11511"]),
 ("q37","comparison","How does the retriever in DPR relate to the retriever used inside RAG?",["2004.04906","2005.11401"]),
 ("q38","comparison","How do Mamba and the Transformer differ in how they scale with sequence length?",["2312.00752","1706.03762"]),
 ("q39","comparison","How does Mixtral's architecture differ from Mistral 7B's?",["2401.04088","2310.06825"]),
 ("q40","comparison","How do the alignment recipes of Llama 2-Chat and InstructGPT differ?",["2307.09288","2203.02155"]),
 ("q41","comparison","How do GQA and Mistral's attention design each speed up inference?",["2305.13245","2310.06825"]),
 ("q42","comparison","Which memory problems do PagedAttention and FlashAttention each address?",["2309.06180","2205.14135"]),
 ("q43","comparison","How do the scaling-laws paper and Chinchilla differ on allocating compute between model size and data?",["2001.08361","2203.15556"]),
 ("q44","comparison","How do BERT and GPT-3 differ in pre-training objective and how they are used on downstream tasks?",["1810.04805","2005.14165"]),
 ("q45","comparison","How do speculative decoding, GQA and PagedAttention each reduce LLM inference cost?",["2211.17192","2305.13245","2309.06180"]),
 ("q46","unanswerable","What GPU hardware did OpenAI use to train GPT-4?",[]),
 ("q47","unanswerable","What MMLU score does Gemini Ultra achieve?",[]),
 ("q48","unanswerable","How does LoRA perform when fine-tuning Stable Diffusion for image generation?",[]),
 ("q49","unanswerable","What was the dollar cost of training Mamba-2?",[]),
 ("q50","unanswerable","What top-1 accuracy does the original Transformer paper report on ImageNet?",[]),
]

# Fill by READING the PDFs (use src/find.py). Format, one entry per question:
#   "q01": {"2106.09685": [<PDF pages where the answer is stated, 1-3 pages>]},
PAGES = {
    "q01": {"2106.09685": [2, 5]}, "q02": {"2305.14314": [4]} ,"q03": {"2305.14314": [5]},"q04": {"2305.18290": [4]},"q05": {"2203.02155": [3]},"q06": {"2212.08073": [5]},"q07": {"2205.14135": [2]},
    "q08": {"2307.08691": [8, 9]}, "q09": {"2210.17323": [4]}, "q10": {"2306.00978": [2]}, "q11": {"2309.06180": [2]}, "q12": {"2211.17192": [11]},
    "q13": {"2305.13245": [2]}, "q14": {"2005.11401": [4]}, "q15": {"2004.04906": [3, 6]}, "q16": {"2310.11511": [1]}, "q17": {"2312.00752": [5]},
    "q18": {"2401.04088": [2]}, "q19": {"2307.09288": [16, 17]}, "q20": {"2310.06825": [1]}, "q21": {"1706.03762": [4]}, "q22": {"1810.04805": [4]},
    "q23": {"2005.14165": [6]}, "q24": {"2001.08361": [20]}, "q25": {"2203.15556": [2]}, "q26": {"2104.09864": [4, 5]}, "q27": {"2309.06180": [1]},
    "q28": {"2203.02155": [8]}, "q29": {"1706.03762": [6]}, "q30": {"1810.04805": [4]}, "q31": {"2106.09685": [2, 5], "2305.14314": [4, 5]},
    "q32": {"2210.17323": [4], "2306.00978": [2]},  "q33": {"2205.14135": [2], "2307.08691": [2, 9]}, "q34": {"2203.02155": [2, 8], "2305.18290": [2, 4]},
    "q35": {"2212.08073": [5], "2203.02155": [8]},  "q36": {"2005.11401": [4], "2310.11511": [1]}, "q37": {"2004.04906": [2], "2005.11401": [3]},
    "q38": {"2312.00752": [1], "1706.03762": [6]}, "q39": {"2401.04088": [1], "2310.06825": [2]}, "q40": {"2307.09288": [14], "2203.02155": [3]},
    "q41": {"2305.13245": [1], "2310.06825": [1, 2]}, "q42": {"2309.06180": [1, 4], "2205.14135": [1]}, "q43": {"2001.08361": [1], "2203.15556": [2]},
    "q44": {"1810.04805": [4, 5], "2005.14165": [1]}, "q45": {"2211.17192": [1, 2], "2305.13245": [1], "2309.06180": [1, 4]},
} 

NOTES = {
    "q01": "LoRA adapts query (Wq) and value (Wv) projections using trainable low-rank matrices while keeping the original pretrained weights frozen.",
    "q02": "NF4 is a 4-bit quantization data type based on quantiles of normally distributed weights. QLoRA uses NF4 for memory-efficient storage of pretrained weights while performing computations in BFloat16 for high-fidelity finetuning.",
    "q03": "Double Quantization quantizes the first-stage quantization constants using a second quantization, reducing storage overhead from 0.5 to 0.127 bits per parameter, saving approximately 0.373 bits per parameter.",
    "q04": "DPO expresses the implicit reward as beta times the log-ratio of learned-policy to reference-policy probabilities, plus a prompt-dependent normalization term that cancels in preference comparisons.",
    "q05": "InstructGPT uses three stages: supervised fine-tuning on human demonstrations, reward model training on human response comparisons, and PPO reinforcement learning to optimize the policy using the learned reward.",
    "q06": "Constitutional AI has two stages: supervised learning using AI-generated critiques and revisions guided by constitutional principles, followed by reinforcement learning using AI-generated preference labels and a preference model.",
    "q07": "FlashAttention uses Theta(N^2*d^2/M) HBM accesses compared with the Omega(N*d + N^2) HBM-access bound stated for standard attention, where N is sequence length, d is head dimension and M is SRAM capacity, under typical parameter assumptions.",
    "q08": "FlashAttention-2 adds sequence-length parallelism across thread blocks to improve GPU occupancy and changes warp partitioning from split-K to split-Q in the forward pass, reducing shared-memory communication and synchronization.",
    "q09": "GPTQ is a one-shot post-training quantization method that uses approximate second-order (inverse-Hessian) information to quantize pretrained weights efficiently, quantizing weights in a fixed order and updating remaining unquantized weights to compensate for quantization error.",
    "q10": "AWQ protects salient channels because a small fraction of important weights strongly affects quantization accuracy. It identifies salient channels using large activation magnitudes rather than weight magnitudes, then applies activation-aware per-channel scaling to reduce quantization error.",
    "q11": "PagedAttention divides the KV cache into fixed-size, non-contiguous blocks. On-demand allocation reduces internal fragmentation, while uniform block sizes eliminate external fragmentation. It also enables block-level memory sharing.",
    "q12": "Speculative decoding accepts draft tokens with probability min(1, p_target/p_draft) and samples rejected tokens from the normalized positive difference between target and draft distributions, mathematically preserving the exact target distribution.",
    "q13": "GQA converts an MHA checkpoint by grouping query heads and mean-pooling the original key and value heads within each group to initialize shared KV heads, followed by additional pretraining to recover quality.",
    "q14": "RAG-Sequence conditions the entire generated sequence on one retrieved document and marginalizes over documents at the sequence level. RAG-Token marginalizes over retrieved documents separately for each token, allowing different documents to contribute to different tokens.",
    "q15": "DPR trains independent BERT question and passage encoders using dot-product similarity and a contrastive negative log-likelihood loss. Negatives include random passages, positives from other questions (in-batch negatives), and high-scoring BM25 passages that do not contain the answer (hard negatives).",
    "q16": "Self-RAG uses reflection tokens for retrieval control and self-critique. Retrieval tokens determine when to retrieve external passages, while critique tokens assess passage relevance, factual support and generation quality.",
    "q17": "Mamba makes SSM parameters Delta, B and C input-dependent, allowing selective propagation or filtering of information. This addresses the inability of time-invariant SSMs to perform content-aware reasoning and selective context compression.",
    "q18": "Mixtral has 8 feedforward experts per MoE layer. A router selects 2 experts for each token, and the layer combines their outputs using a weighted sum.",
    "q19": "Ghost Attention improves multi-turn instruction consistency in Llama 2-Chat. It constructs synthetic dialogues by repeating initial instructions across user turns, then retains the instruction in the first turn and masks loss on preceding turns during fine-tuning.",
    "q20": "Mistral 7B combines Grouped-Query Attention (GQA) for faster inference and lower KV-cache memory requirements with Sliding Window Attention (SWA) for efficient processing of longer sequences at reduced computational cost.",
    "q21": "Scaled dot-product attention computes softmax(QK^T/sqrt(d_k))V. Scaling by sqrt(d_k) prevents large dot products from saturating softmax and producing extremely small gradients.",
    "q22": "BERT uses Masked Language Modeling (MLM), predicting selected masked tokens using bidirectional context, and Next Sentence Prediction (NSP), a binary classification task predicting whether sentence B follows sentence A.",
    "q23": "GPT-3 defines few-shot in-context learning as providing K task demonstrations (typically 10-100 input-output examples) in the prompt, followed by a new input whose completion the model predicts without any gradient updates or fine-tuning.",
    "q24": "Test loss follows approximate power laws with model size N, dataset size D, and training compute C, with respective exponents 0.076, 0.095, and 0.057 in the paper's summary. Larger scale reduces loss with diminishing returns under the specified regimes.",
    "q25": "Compute-optimal training minimizes loss by jointly choosing model size and training tokens under a fixed FLOP budget. Chinchilla uses 70B parameters and 1.4T tokens, approximately 20 tokens per parameter; this ratio is not a universal optimum.",
    "q26": "RoPE encodes absolute token positions by rotating query and key vectors through position-dependent angles. Their attention dot product depends on the relative positional difference (m-n), enabling relative-position awareness.",
    "q27": "The KV cache stores previously computed attention keys and values for reuse during autoregressive generation. It grows with generated tokens and concurrent requests, consuming substantial dynamic GPU memory and limiting batching and serving throughput.",
    "q28": "InstructGPT trains a scalar reward model initialized from the SFT model using human rankings of 4-9 responses per prompt. A pairwise logistic loss encourages higher rewards for preferred responses, with comparisons from each prompt grouped during training.",
    "q29": "Per-layer computational complexity is O(n^2*d) for self-attention, O(n*d^2) for recurrent layers, and O(k*n*d^2) for convolutional layers, where n is sequence length, d is representation dimension, and k is convolution kernel size.",
    "q30": "BERT randomly selects 15% of tokens for MLM prediction. Of these, 80% are replaced with [MASK], 10% with a random token, and 10% remain unchanged. The model predicts the original tokens.",
    "q31": "LoRA freezes the pretrained base weights and trains low-rank adapters, reducing optimizer-state and gradient memory without requiring base-weight quantization. QLoRA additionally stores the frozen base weights in 4-bit NF4, dequantizes them to BF16 for computation, and trains LoRA adapters, further reducing memory requirements.",
    "q32": "GPTQ uses approximate second-order Hessian information and error compensation to quantize pretrained weights. AWQ instead uses activation magnitudes to identify salient channels and applies per-channel scaling to protect them, without backpropagation or weight reconstruction.",
    "q33": "FlashAttention uses IO-aware tiling to reduce HBM accesses while computing exact attention. FlashAttention-2 improves it by reducing non-matmul FLOPs, adding sequence-length parallelism across thread blocks, and changing forward-pass warp partitioning from split-K to split-Q to reduce communication and shared-memory operations.",
    "q34": "InstructGPT uses supervised fine-tuning, explicit reward model training on human comparisons, and PPO reinforcement learning. DPO instead directly optimizes the policy using preference pairs and a classification loss, eliminating separate reward-model training and PPO.",
    "q35": "Constitutional AI uses AI-generated preference labels guided by constitutional principles for harmlessness, combined with human preference labels for helpfulness. InstructGPT trains its reward model using human-ranked response comparisons.",
    "q36": "Original RAG retrieves a fixed top-K set of passages for an input and marginalizes over them during generation. Self-RAG adaptively decides whether and when to retrieve using reflection tokens, avoiding unnecessary retrieval.",
    "q37": "DPR trains a dense question-passage bi-encoder using contrastive learning. RAG initializes its retriever and document index from pretrained DPR, then jointly trains the retriever with its BART generator for retrieval-augmented generation.",
    "q38": "Mamba uses selective state space models with linear scaling in sequence length and efficient recurrent inference. Standard Transformer self-attention has quadratic O(n^2*d) per-layer complexity and requires a growing KV cache during autoregressive inference.",
    "q39": "Mistral 7B is a dense Transformer, while Mixtral uses a Sparse Mixture-of-Experts architecture with 8 feedforward experts per layer, routing each token to 2 experts. Mixtral otherwise largely retains Mistral 7B's underlying architecture.",
    "q40": "InstructGPT uses SFT, a human-preference reward model, and PPO. Llama 2-Chat uses SFT followed by iterative RLHF with separate helpfulness and safety reward models, rejection-sampling fine-tuning, and later PPO, including distillation from its 70B model.",
    "q41": "GQA shares KV heads across groups of query heads to reduce decoding memory bandwidth. Mistral uses GQA alongside sliding-window attention to reduce attention computation and a fixed-size rolling KV cache to reduce memory usage.",
    "q42": "PagedAttention addresses KV-cache fragmentation, preallocation waste, and redundant duplication using paging-inspired memory management. FlashAttention addresses excessive HBM-SRAM memory transfers during attention using IO-aware tiling.","q42": "PagedAttention addresses KV-cache fragmentation, preallocation waste, and redundant duplication using paging-inspired memory management. FlashAttention addresses excessive HBM-SRAM memory transfers during attention using IO-aware tiling.",
    "q43": "Kaplan et al. favor allocating compute toward very large models trained on relatively modest data, stopping before convergence. Chinchilla revises this allocation toward smaller models trained on substantially more tokens, finding that model size and training tokens should scale approximately equally with compute.",
    "q44": "BERT uses bidirectional masked language modeling and next sentence prediction during pre-training, then fine-tunes all parameters for downstream tasks. GPT-3 uses autoregressive language modeling and performs tasks through few-shot in-context examples without gradient updates.",
    "q45": "Speculative decoding accelerates generation by drafting tokens with a smaller model and verifying them in parallel with the target model while preserving its output distribution. GQA reduces KV-cache memory bandwidth by sharing key-value heads across query groups. PagedAttention reduces KV-cache fragmentation and memory waste through paging-inspired management, enabling larger batches and higher serving throughput.",    
}

meta = json.load(open("data/meta.json"))
npages = {m["arxiv_id"]: m["pages"] for m in meta.values()}
rows, missing = [], []
for qid, typ, q, papers in QUESTIONS:
    pg = PAGES.get(qid, {})
    for p in papers:
        assert p in npages, f"{qid}: unknown paper {p}"
        if not pg.get(p):
            missing.append((qid, p))
        for n in pg.get(p, []):
            assert 1 <= n <= npages[p], f"{qid}: page {n} out of range for {p}"
    rows.append({"id": qid, "question": q, "type": typ, "answerable": typ != "unanswerable",
                 "gold_papers": papers, "gold_pages": pg, "reference_notes": NOTES.get(qid, "")})

with open("eval/gold.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(dict(Counter(r["type"] for r in rows)), "| total", len(rows))
print(f"missing gold pages: {len(missing)}", missing[:8])
if "--strict" in sys.argv and missing:
    sys.exit(1)
