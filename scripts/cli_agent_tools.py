import sys
import os
import json
import argparse

# Force utf-8 for stdout on windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm thư mục root vào sys.path để có thể import từ evaluator
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Setup Django (nếu cần thiết, dù mcda_engine không thực sự dùng ORM)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
try:
    import django
    django.setup()
except Exception:
    pass

from evaluator.agent_tools import (
    verify_declared_skills_tool,
    evaluate_preliminary_fit_tool,
    generate_topic_deep_quiz_tool,
    parse_member_profile_tool
)

def main():
    parser = argparse.ArgumentParser(description="MatchSkill AI - Agent CLI Tools")
    parser.add_argument('tool_name', type=str, help='Tên công cụ cần chạy (ví dụ: verify_skills, evaluate_mcda, get_topics)')
    parser.add_argument('--kwargs', type=str, default='{}', help='JSON chuỗi chứa các tham số (kwargs)')
    
    args = parser.parse_args()
    
    try:
        kwargs = json.loads(args.kwargs)
    except Exception as e:
        print(json.dumps({"error": f"Lỗi parse JSON kwargs: {e}"}, ensure_ascii=False))
        return

    result = {}
    
    try:
        if args.tool_name == "verify_skills":
            # kwargs cần có "declared_skills"
            declared_skills = kwargs.get("declared_skills", [])
            result = verify_declared_skills_tool(declared_skills)
            
        elif args.tool_name == "evaluate_mcda":
            # kwargs cần có "team_members" và "topic"
            team_members = kwargs.get("team_members", [])
            topic = kwargs.get("topic", {})
            result = evaluate_preliminary_fit_tool(team_members, topic)
            
        elif args.tool_name == "generate_deep_quiz":
            result = generate_topic_deep_quiz_tool(**kwargs)
            
        elif args.tool_name == "parse_profile":
            result = parse_member_profile_tool(**kwargs)
            
        elif args.tool_name == "get_topic_by_keyword":
            # Công cụ phụ: Đọc file topics_data.json và filter
            keyword = kwargs.get("keyword", "").lower()
            topic_data_path = os.path.join(project_root, "topics_data.json")
            if os.path.exists(topic_data_path):
                with open(topic_data_path, "r", encoding="utf-8") as f:
                    topics = json.load(f)
                
                matched_topics = []
                for t in topics:
                    code = str(t.get("code", "")).lower()
                    cat = str(t.get("category", "")).lower()
                    desc = str(t.get("description", "")).lower()
                    req = str(t.get("requirements", "")).lower()
                    if keyword in code or keyword in cat or keyword in desc or keyword in req:
                        matched_topics.append(t)
                
                # Trả về top 5 để LLM không bị quá tải context
                result = {"status": "success", "count": len(matched_topics), "topics": matched_topics[:5]}
            else:
                result = {"error": "Không tìm thấy file topics_data.json"}
        else:
            result = {"error": f"Không tìm thấy tool: {args.tool_name}"}
            
    except Exception as e:
        result = {"error": str(e)}

    # In kết quả dạng JSON để AI đọc được
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
