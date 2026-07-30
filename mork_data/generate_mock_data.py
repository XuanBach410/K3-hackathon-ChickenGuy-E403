import asyncio
import json

from openai import AsyncOpenAI

# API key from QwenCloud
API_KEY = "sk-ws-H.XEXLID.QTgJ.MEUCIQDqQtS_NR7Cw2c8WPlJUo4JvzKharOKpCI0-4gcw_snfAIgcks7DNKnJJm2itoSQ-JrjVqze-FiZnKFuDPspfQ-LL4"

client = AsyncOpenAI(
    api_key=API_KEY, base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

SYSTEM_PROMPT = """Bạn là một chuyên gia tạo dữ liệu mock (dữ liệu giả lập) cho hệ thống hồ sơ năng lực nhân sự.
Dữ liệu cần trả về 100% dưới định dạng JSON array hợp lệ. Không được chứa markdown code blocks (như ```json) ở đầu và cuối, chỉ cần trả về mảng JSON thuần túy.

Cấu trúc mỗi object trong JSON như sau:
{
  "name": "Nguyễn Văn Nghĩa", // Tạo một họ và tên người Việt Nam ngẫu nhiên hợp lệ
  "skills": {
    "engineering": ["Frontend", "Backend", "Mobile", "DevOps/Cloud"], // Chọn 1-4
    "ai_data": ["Machine Learning", "NLP", "Computer Vision", "Data Analysis", "Data Engineering", "Prompt Engineering"], // Chọn 0-6
    "product": ["Product Management", "Business Analysis", "User/Market Research"], // Chọn 0-3
    "design": ["UI/UX Design", "Graphic Design"], // Chọn 0-2
    "leadership": ["Project Management", "Team Leadership", "Communication"] // Chọn 0-3
  },
  "proficiency": {
    // Chỉ chứa các kỹ năng đã được chọn ở trên. Value từ 1 đến 5 (1=Cơ bản, 5=Chuyên gia).
    // Ví dụ: "Backend": 3, "NLP": 4, "Team Leadership": 3
  },
  "desired_roles": ["Product Owner", "Tech Lead", "Data/AI"], // Chọn ngẫu nhiên từ: Product Owner, Project Manager, Tech Lead, Developer, Designer, Data/AI, Business Analyst
  "fields_of_interest": ["Nông nghiệp", "Y tế & Sức khỏe"], // Chọn ngẫu nhiên từ: Nông nghiệp, Giáo dục & Đào tạo, Ngân hàng & Tài chính, Y tế & Sức khỏe, Phòng chống Thiên tai, Đổi mới Sáng tạo, Chính phủ Thông minh, Năng suất Doanh nghiệp Vừa & Nhỏ
  "current_industry": "IT", // Ví dụ: IT, Finance, Education...
  "years_of_experience": 3, // Số nguyên từ 0 đến 20
  "hours_per_week": 40, // Số nguyên từ 10 đến 60
  "introduction": "Giới thiệu ngắn gọn về bản thân (khoảng 3-4 câu tiếng Việt)."
}

Hãy sinh ra chính xác 20 đối tượng JSON (20 người khác nhau) trong mảng. Đảm bảo dữ liệu đa dạng và hợp lý.
"""


async def generate_batch():
    try:
        response = await client.chat.completions.create(
            model="qwen-plus",  # Dùng qwen-plus cho tác vụ này
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "Tạo cho tôi 20 hồ sơ. Chỉ trả về mảng JSON.",
                },
            ],
            temperature=0.8,
        )
        content = response.choices[0].message.content.strip()

        # Làm sạch kết quả trả về trong trường hợp mô hình vẫn thêm markdown
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        content = content.removesuffix("```")

        return json.loads(content.strip())
    except Exception as e:
        print(f"Error generating batch: {e}")
        return []


async def main():
    total_records = 100
    batch_size = 20
    batches = total_records // batch_size

    all_data = []

    print(f"Bắt đầu tạo {total_records} dữ liệu mock qua {batches} batch...")

    # Chạy các batch đồng thời hoặc tuần tự
    # Để an toàn với rate limit, chạy tuần tự
    for i in range(batches):
        print(f"Đang xử lý batch {i + 1}/{batches}...")
        batch_data = await generate_batch()
        if batch_data:
            all_data.extend(batch_data)
            print(f"Đã nhận {len(batch_data)} bản ghi từ batch {i + 1}.")
        else:
            print(f"Batch {i + 1} trả về rỗng do lỗi.")

    # Đảm bảo đủ số lượng (trong trường hợp có lỗi)
    all_data = all_data[:total_records]

    output_file = "mock_profiles.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\nĐã tạo thành công {len(all_data)} bản ghi và lưu vào {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
