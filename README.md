# Your Project Name

Welcome to your new FastAPI project! 🎉

This is your project's main README file - feel free to customize it to describe what your application does, how to use it, and any specific features you've built.

## 🎯 Creating Your Own Project from This Template

**This is a FastAPI template!** If you want to create your own project (let's say "My Awesome Project"), here's exactly how to do it:

### Step 1: Get the Template
First, you need to get this template. You can either:
- Clone the repository: `git clone <template-repo-url>`
- Download it as a ZIP file
- Or use it as a GitHub template

### Step 2: Copy and Rename
Copy the entire template folder and rename it to your project name (e.g., `myawesomeproject_backend`).

### Step 3: Run the Customization Script
This is where the magic happens! Run:
```bash
./scripts/customize_template.sh
```

The script will ask you questions like:
- "What's your project name?" → "My Awesome Project"
- "What should the project slug be?" → "myawesomeproject_backend"
- "What should the database be called?" → "myawesomeproject_backend"

### Step 4: The Magic Happens
The script automatically:
- Renames all template references to your project name
- Updates database names and connection strings
- Changes import statements throughout the code
- Updates documentation and README files
- Modifies configuration files
- Updates the Docker setup

### Step 5: Set Up Your New Project
After customization, run:
```bash
./scripts/setup_comprehensive.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Set up your `.env` file with the right database name
- Start PostgreSQL and Redis
- Run database migrations
- Verify everything works

### Step 6: Start Building!
Now you have a fully working project with:
- User authentication system
- Admin panel
- API key management
- Database setup
- Testing framework
- Docker support
- All template features, but branded for your project

**That's it!** You've gone from "I want to build My Awesome Project" to "I have a working My Awesome Project API" in just a few commands.

## 🚀 Getting Started

If you're new to this project, here's how to get it running:

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Redis (optional, for caching)

### Quick Setup

**Option 1: Automated Setup (Recommended)**
```bash
# Run the comprehensive setup script
./scripts/setup_comprehensive.sh
```
This script will automatically:
- Create a virtual environment
- Install dependencies
- Set up your `.env` file
- Start the database
- Run migrations
- Verify everything is working

**Option 2: Manual Setup**
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and other settings
   ```

3. **Set up the database:**
   ```bash
   # Run database migrations
   alembic upgrade head
   ```

4. **Start your application:**
   ```bash
   uvicorn app.main:app --reload
   ```

Your API will be available at `http://localhost:8000`

Visit http://localhost:8000/docs to view the interactive API documentation.

## 📚 API Documentation

Once your app is running, you can explore your API:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 🐳 Running with Docker

If you prefer using Docker:

```bash
# Start everything with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🧪 Testing Your Application

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app
```

## 🔧 Development Workflow

```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Format your code
ruff format .

# Check for code issues
ruff check .
```

## 🧹 Code Quality (Pre-commit Hooks)

This project uses [pre-commit](https://pre-commit.com/) hooks for code quality. To set them up:

```bash
./scripts/install_precommit.sh
```

This script will:
- Install pre-commit
- Install git hooks for code formatting and linting
- Run all hooks on your codebase

You can also manually install the hooks:
```bash
pre-commit install
```

The pre-commit hooks will automatically:
- Format your code with `black`
- Check for linting issues with `ruff`
- Verify type annotations with `mypy`
- Run on every commit to ensure code quality

## 📖 What's Included

This project comes with several features out of the box:

- **User Authentication** - Registration, login, and JWT tokens
- **Database Management** - PostgreSQL with automatic migrations
- **Admin Panel** - Built-in admin interface at `/admin`
- **API Key Management** - Secure API key system
- **Audit Logging** - Track important actions
- **Testing Framework** - Comprehensive test suite
- **Docker Support** - Easy containerized deployment

## 🎯 Next Steps

If you're using this as a template to create your own project, follow the steps above in the "Creating Your Own Project from This Template" section.

If you're already working with your customized project:

1. **Customize this README** - Update it to describe your specific project
2. **Explore the code** - Check out the `app/` folder to see how everything is organized
3. **Add your features** - Start building your application logic
4. **Check the docs** - See the template documentation for advanced features

## 📚 Template Documentation

This project was built using a FastAPI template that provides a solid foundation. For detailed information about:

- Template features and capabilities
- Advanced configuration options
- Deployment guides
- Troubleshooting tips

**Check out the documentation in the `docs/` folder:**
- [Template Overview](docs/TEMPLATE_README.md)
- [Getting Started Guide](docs/tutorials/getting-started.md)
- [Complete Tutorials](docs/tutorials/TUTORIALS.md)

## 🤝 Contributing

This is your project! Feel free to:
- Add new features
- Modify existing code
- Update documentation
- Add tests for your changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note**: This is a default MIT license. You may want to update it to reflect your specific licensing needs for your project.

---

**Happy coding! 🚀**

*This project was created using a FastAPI template. For template-specific information, see the `docs/` folder.* 