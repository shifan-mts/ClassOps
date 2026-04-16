# 🎓 ClassOps – Teacher Workflow Automation Platform

**ClassOps** is a full-stack platform that helps educators automate attendance, assignments, and academic tracking—saving time and improving student insights.

---

## 🚀 Features

- 📊 Dashboard for classes, alerts, and progress  
- 🧾 Attendance tracking with low-attendance detection (<75%)  
- 📚 Google Classroom sync for assignments and students  
- 📈 Student performance analytics (marks + attendance)  
- 📘 Syllabus progress tracking  
- 📝 Question paper generator (Bloom’s Taxonomy)  
- 🤖 AI plagiarism & usage detection  

---

## 🏗 Tech Stack

- **Frontend:** React (Vite), TailwindCSS  
- **Backend:** Flask (Python)  
- **Database:** SQLite (SQLAlchemy ORM)  
- **Integrations:** Google OAuth, Google Classroom API  

---

## ⚙️ Setup (Single Command)

```bash
git clone https://github.com/your-username/classops.git && cd classops && \
cd Backend && pip install -r requirements.txt && python app.py & \
cd ../Frontend && npm install && npm run dev