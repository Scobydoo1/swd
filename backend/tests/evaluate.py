"""Đánh giá chatbot trên test set 50 câu hỏi.

Cách dùng:
    python -m tests.evaluate --course-id 1

Quy trình:
1. Đọc test_set.json.
2. Với mỗi câu hỏi: gọi RAG pipeline (retrieve + LLM) để lấy câu trả lời của bot.
3. Dùng LLM-as-judge so sánh câu trả lời của bot với ground_truth -> điểm 0..1 + verdict.
4. In bảng kết quả + accuracy tổng thể, lưu eval_result.json.

Yêu cầu: đã seed môn học và index tài liệu vào ChromaDB trước đó.
"""
import argparse
import json
import os

from app.database import SessionLocal
from app.llm.client import LlmClient
from app.modules.chat.schemas import ChatRequest
from app.modules.chat.service import ChatService

HERE = os.path.dirname(os.path.abspath(__file__))

JUDGE_PROMPT = """Bạn là giám khảo chấm điểm câu trả lời của chatbot.
So sánh CÂU TRẢ LỜI với ĐÁP ÁN ĐÚNG (ground truth) cho cùng một CÂU HỎI.

Chấm điểm từ 0.0 đến 1.0 dựa trên mức độ chính xác về mặt nội dung (không cần khớp từng chữ):
- 1.0: đúng và đầy đủ ý chính.
- 0.5: đúng một phần.
- 0.0: sai hoặc không trả lời được.

Trả về DUY NHẤT một JSON: {"score": <float>, "verdict": "<correct|partial|incorrect>", "reason": "<ngắn gọn>"}"""


def judge(llm: LlmClient, question: str, answer: str, truth: str) -> dict:
    content = (
        f"CÂU HỎI: {question}\n\n"
        f"ĐÁP ÁN ĐÚNG: {truth}\n\n"
        f"CÂU TRẢ LỜI CỦA BOT: {answer}"
    )
    raw = llm.chat(
        [
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0,
    )
    try:
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": 0.0, "verdict": "incorrect", "reason": "Không parse được"}


def run(course_id: int | None):
    with open(os.path.join(HERE, "test_set.json"), encoding="utf-8") as f:
        test_set = json.load(f)

    db = SessionLocal()
    chat = ChatService(db)
    llm = LlmClient()
    results = []
    total = 0.0

    try:
        for item in test_set["items"]:
            resp = chat.answer(
                ChatRequest(question=item["question"], course_id=course_id),
                user_id=None,
            )
            verdict = judge(llm, item["question"], resp.answer, item["ground_truth"])
            total += verdict["score"]
            results.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "bot_answer": resp.answer,
                    "ground_truth": item["ground_truth"],
                    **verdict,
                }
            )
            print(f"[{item['id']:2}] {verdict['verdict']:9} ({verdict['score']}) - {item['question'][:50]}")
    finally:
        db.close()

    n = len(results)
    accuracy = total / n if n else 0
    summary = {
        "total_questions": n,
        "average_score": round(accuracy, 4),
        "correct": sum(1 for r in results if r["verdict"] == "correct"),
        "partial": sum(1 for r in results if r["verdict"] == "partial"),
        "incorrect": sum(1 for r in results if r["verdict"] == "incorrect"),
        "results": results,
    }
    with open(os.path.join(HERE, "eval_result.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n===== KẾT QUẢ =====")
    print(f"Số câu: {n}")
    print(f"Điểm trung bình (accuracy): {accuracy:.2%}")
    print(f"Correct: {summary['correct']} | Partial: {summary['partial']} | Incorrect: {summary['incorrect']}")
    print("Chi tiết lưu tại tests/eval_result.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", type=int, default=None)
    args = parser.parse_args()
    run(args.course_id)
