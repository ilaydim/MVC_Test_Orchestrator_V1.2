# 🎯 MVC Test Orchestrator v1.2 - Simple Edition

**AI-powered MVC code generator for learning projects**

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
# Create .env file
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### 3. Use in VS Code
```
@mvc /create-srs Simple blog with posts and comments
@mvc /extract
@mvc /scaffold
@mvc /code
```

---

## 📊 What Gets Generated

### **Simple Project Structure**:
- ✅ **5-8 Models** (not 17!)
- ✅ **4-6 Controllers** (not 14!)
- ✅ **4-6 Views** (not 14!)
- ✅ **Total: 15-20 files** (manageable!)

### **Generated Code**:
- Simple, clean Python classes
- 20-40 lines per file
- No complex logic
- Perfect for learning

---

## 🎓 Learning-Focused

This tool creates **simple, understandable code** for:
- Computer Science students
- Python learners
- MVC pattern practice
- Quick prototyping

**NOT for production!** This is an educational tool.

---

## 💡 Key Features

✅ Interactive SRS creation (5 questions)  
✅ Smart architecture extraction  
✅ Clean MVC code generation  
✅ Work package system (Models → Controllers → Views)  
✅ Hallucination checking  
✅ VS Code integration  

---

## 📝 Example Workflow

### Input:
```
@mvc /create-srs Task manager for students
```

### Output Structure:
```
generated_src/
├── models/
│   ├── User.py          (id, name, email)
│   ├── Task.py          (id, title, deadline, status)
│   └── Category.py      (id, name, color)
├── controllers/
│   ├── UserController.py
│   ├── TaskController.py
│   └── AuthController.py
└── views/
    ├── TaskListView.py
    ├── TaskDetailView.py
    └── UserProfileView.py
```

**Total: ~8 files** (not 45!)

---

## ⚙️ Configuration

### Limits (Set in prompts):
- **Models**: Max 8
- **Controllers**: Max 6
- **Views**: Max 6
- **Actions per controller**: 3-5
- **Lines per file**: 20-40

### Why These Limits?
1. **Faster generation** (2-3 min vs 6+ min)
2. **Lower API costs** (15-20 requests vs 45)
3. **Easier to understand** (learning project)
4. **Better quality** (focused code)

---

## 🔧 Troubleshooting

### Problem: "Only 1 file generated"
**Cause**: API quota exceeded  
**Solution**: 
- Wait 24 hours
- OR use new API key

### Problem: "Permission denied"
**Solution**: Run as Administrator (Windows)

### Problem: "Too complex architecture"
**Solution**: Regenerate SRS with simpler description

---

## 📚 Documentation

- `.github/prompts/` - All AI prompts (editable!)
- `scaffolds/mvc_skeleton/` - Template files (read-only)
- `generated_src/` - Your generated code

---

## 🎯 Best Practices

### ✅ Good SRS Descriptions:
```
"Blog with posts and comments"
"Task manager for students"
"Simple e-commerce with cart"
```

### ❌ Avoid:
```
"Full-featured social network with messaging, stories, ..."
"Enterprise ERP system with ..."
"Complex marketplace with ..."
```

**Keep it simple!** This is for learning.

---

## 🚦 System Requirements

- Python 3.9+
- VS Code with Copilot
- Google Gemini API key (free tier OK)
- ~500MB disk space

### Model Configuration

Default model: `gemini-2.5-flash`

To change model, edit `src/core/config.py`:
- `gemini-2.5-flash` - Default (current working model)
- `gemini-1.5-flash` - Alternative
- `gemini-pro` - Older but stable

---

## 📞 Support

**VS Code Output**: View → Output → "MVC Orchestrator"  
**Python Errors**: Check terminal output

---

**Made for learners, by learners. Keep it simple!** 🎓
