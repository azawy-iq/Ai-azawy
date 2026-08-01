import streamlit as st
import google.generativeai as genai
import json
import base64
import requests

st.set_page_config(page_title="صانع التطبيقات الذكي", page_icon="🚀", layout="centered")

st.title("🚀 صانع التطبيقات الذكي (AI App Generator)")
st.write("أدخل بيانات تطبيقك لإنشاء كوده ورفعه إلى GitHub لبناء ملف IPA سحابياً.")

# المدخلات الأساسية
app_name = st.text_input("اسم التطبيق (بالإنجليزي بدون مساحات):", "MyAiApp")
user_prompt = st.text_area("صف التطبيق والمميزات التي تريدها:", "تطبيق إدارة مهام يومية بسيط وعصري.")
uploaded_image = st.file_uploader("ارفع صورة لتصميم الواجهة (اختياري):", type=["png", "jpg", "jpeg"])

gemini_key = st.text_input("أدخل Gemini API Key:", type="password")
github_token = st.text_input("أدخل GitHub Personal Access Token:", type="password")

if st.button("🏗️ توليد التطبيق ورفعه إلى GitHub"):
    if not all([app_name, user_prompt, gemini_key, github_token]):
        st.error("يرجى ملء جميع الحقول المطلوبة المفاتيح والبيانات.")
    else:
        with st.spinner("جاري تحليل الطلب وإنشاء الملفات بواسطة الذكاء الاصطناعي..."):
            try:
                # إعداد الذكاء الاصطناعي
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')

                # التوجيه الصارم لتوليد البنية
                system_instruction = f"""
                أنت مهندس تطبيقات iOS. أنشئ مشروع SwiftUI متكامل باسم '{app_name}'.
                يجب أن ترجع الرد بصيغة JSON فقط بالتنسيق التالي:
                {{
                  "files": [
                    {{"path": "{app_name}/AppMain.swift", "content": "..."}},
                    {{"path": "{app_name}/ContentView.swift", "content": "..."}},
                    {{"path": "{app_name}.xcodeproj/project.pbxproj", "content": "..."}},
                    {{"path": ".github/workflows/build_ipa.yml", "content": "..."}}
                  ]
                }}
                تأكد من إدراج ملف .github/workflows/build_ipa.yml بالمسار الصحيح لبناء IPA.
                """

                inputs = [system_instruction, user_prompt]
                if uploaded_image:
                    inputs.append({"mime_type": uploaded_image.type, "data": uploaded_image.getvalue()})

                response = model.generate_content(inputs)
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                project_data = json.loads(clean_json)

                # إنشاء المستودع في GitHub
                headers = {"Authorization": f"token {github_token}"}
                repo_res = requests.post(
                    "https://api.github.com/user/repos", 
                    json={"name": app_name, "private": False}, 
                    headers=headers
                ).json()

                if "owner" in repo_res:
                    username = repo_res['owner']['login']
                    progress = st.progress(0)
                    files = project_data['files']

                    # رفع الملفات ملفاً تلو الآخر
                    for idx, f in enumerate(files):
                        file_url = f"https://api.github.com/repos/{username}/{app_name}/contents/{f['path']}"
                        content_b64 = base64.b64encode(f['content'].encode('utf-8')).decode('utf-8')
                        payload = {"message": f"Add {f['path']}", "content": content_b64}
                        requests.put(file_url, json=payload, headers=headers)
                        progress.progress((idx + 1) / len(files))

                    st.success(f"🎉 تم إنشاء المستودع ورفع الملفات بنجاح!")
                    st.markdown(f"🔗 [رابط المشروع على GitHub](https://github.com/{username}/{app_name})")
                    st.info("💡 سيتم الآن بناء ملف הـ IPA سحابياً تلقائياً، يمكنك تنزيله من تبويب Actions من المستودع أعلاه.")
                else:
                    st.error("فشل في إنشاء المستودع، تأكد من صلاحيات الـ GitHub Token.")

            except Exception as e:
                st.error(f"حدث خطأ: {e}")
