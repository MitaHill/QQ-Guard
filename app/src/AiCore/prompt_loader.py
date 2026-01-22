import glob
import os


def load_prompt(prompt_dir: str, prompt_file: str) -> str:
    """加载知识库和提示词"""
    knowledge_content = ""

    if not prompt_dir:
        print("⚠️ 未提供提示词语料目录，跳过知识库加载")
    elif os.path.exists(prompt_dir):
        txt_files = glob.glob(os.path.join(prompt_dir, "*.txt"))
        for file_path in txt_files:
            filename = os.path.basename(file_path)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    knowledge_content += f"{filename}的内容\n{content}\n\n"
                    print(f"加载知识库: {filename}")
            except Exception as exc:
                print(f"读取文件失败 {filename}: {exc}")
    else:
        print(f"⚠️ 知识库目录不存在: {prompt_dir}")

    main_prompt = ""
    if not prompt_file:
        print("⚠️ 未提供主提示词路径，提示词为空")
    elif os.path.exists(prompt_file):
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                main_prompt = f.read().strip()
                print(f"加载主提示词: {prompt_file}")
        except Exception as exc:
            print(f"读取提示词失败: {exc}")
    else:
        print(f"⚠️ 主提示词文件不存在: {prompt_file}")

    full_prompt = knowledge_content + main_prompt
    print(f"知识库拼接完成，总长度: {len(full_prompt)} 字符")
    return full_prompt
