import os
import subprocess
import glob

DOCS_DIR = "/Volumes/Data/Haravan/frappe_login_with_haravan/docs/customer-guide"

PROMPT = """Bạn là một chuyên gia UX Writing và Content Strategy theo phương pháp StoryBrand. Bạn đóng vai trò là "Người Hướng Dẫn" (Guide) giúp Khách Hàng (Hero) giải quyết vấn đề của họ trên Cổng Hỗ Trợ Haravan (Helpdesk).

Nhiệm vụ của bạn là viết lại bài hướng dẫn (KB article) dưới đây sao cho:
1. Dễ hiểu, thân thiện, và bớt tính kỹ thuật (less tech jargon).
2. Viết bằng tiếng Việt chuyên nghiệp, tự nhiên, thấu cảm.
3. Đổi tiêu đề chính (H1) thành một câu rõ ràng, hướng tới hành động (VD: "Hướng dẫn...", "Cách để...").
4. **QUAN TRỌNG NHẤT**: KHÔNG ĐƯỢC xóa bỏ bất kỳ bước hướng dẫn, thông tin kỹ thuật, bảng (tables), hình ảnh, liên kết (links), hay các khối Alert của VitePress (như `::: info`, `::: tip`, `::: warning`). Phải giữ nguyên cấu trúc Markdown của chúng, chỉ viết lại lời văn xung quanh cho dễ hiểu.
5. Sử dụng bullet points hoặc in đậm các từ khóa quan trọng (như tên nút, menu) để người dùng dễ theo dõi.

CHỈ TRẢ VỀ NỘI DUNG MARKDOWN (không bọc trong tag ```markdown). Đừng thêm bất kỳ giải thích nào khác.

Nội dung cần viết lại:
"""

def rewrite_file(filepath):
    print(f"Processing: {os.path.basename(filepath)}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    full_prompt = PROMPT + "\n\n" + content

    try:
        # Gọi lệnh gemini CLI
        result = subprocess.run(
            ["gemini", "--skip-trust", full_prompt],
            capture_output=True,
            text=True,
            check=True
        )

        rewritten = result.stdout.strip()

        # Lọc bỏ code block markdown nếu gemini trả về
        if rewritten.startswith("```markdown"):
            rewritten = rewritten[11:]
        elif rewritten.startswith("```"):
            rewritten = rewritten[3:]

        if rewritten.endswith("```"):
            rewritten = rewritten[:-3]

        rewritten = rewritten.strip()

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(rewritten)

        print(f"✅ Xong: {os.path.basename(filepath)}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi xử lý {os.path.basename(filepath)}:")
        print(e.stderr)

def main():
    md_files = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    for md_file in md_files:
        rewrite_file(md_file)

if __name__ == "__main__":
    main()
