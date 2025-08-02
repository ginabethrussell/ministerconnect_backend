# MinisterConnect Backend

MinisterConnect is a Django REST API backend supporting a platform that connects ministry candidates with churches. This repository handles core functionality such as user authentication, role-based access control, candidate profiles, job listings, and mutual interest tracking.

## 📌 Features

- Role-based user accounts (`candidate`, `church`, `admin`, `superadmin`)
- Invite-code based registration
- Candidate profile creation, editing, submission, and admin approval
- Church job listing creation and management
- Mutual interest system (churches and candidates)
- Password reset flow using temporary credentials
- Candidate profile image or resume pdf upload (local or AWS S3)
- Admin management via Django admin
- Swagger/OpenAPI documentation

## ⚙️ Tech Stack

- Python 3.10+
- Django 4.x
- Django REST Framework
- PostgreSQL
- AWS S3 for media storage
- drf-spectacular for API schema generation
- Render for deployment

## 🛠️ Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ginabethrussell/ministerconnect_backend.git
cd ministerconnect_backend
```

### 2. Set Up the Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

```bash
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost/dbname
AWS_ACCESS_KEY_ID=your-key-id
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=your-region-name
```

### 5. Run Migrations & Start Server

```bash
make migrate
make run
```

## 🧪 Running Tests

```bash
make test
```

## 📘 API Documentation

- API documentation is auto-generated with drf-spectacular.

### View Locally

- Swagger UI Schema Download YML: http://localhost:8000/api/schema/
- Swagger API Docs: http://localhost:8000/api/docs/

### Published Docs

- [![View API Docs](https://img.shields.io/badge/View-API_Docs-blue)](https://minister-connect-backend.onrender.com/api/docs/)

## 👥 User Roles (Groups) & Permissions

| Role       | Capabilities                                                                                      |
| ---------- | ------------------------------------------------------------------------------------------------- |
| Candidate  | Register via invite code, create/edit profile, express interest in jobs                           |
| Church     | Update church, add church users, post jobs, express interest in candidates, view mutual interests |
| Admin      | Manage churches and invite codes, review/approve candidate profiles , review/approve jobs         |
| Superadmin | Full access including invite code generation and admin functions                                  |

## 🗂️ Project Structure

```bash
ministerconnect_backend/
├── api/                # models, serializers, views, urls, migrations, tests
├── ministerconnect_backend/ # settings
├── Makefile            # terminal command shortcuts
├── README              # project description
└── requirements.txt    # project dependencies
```

## 🚀 Deployment & Hosting

- This backend is deployed using Render with the following infrastructure:

### ⚙️ Services

| Component          | Provider             | Notes                                         |
| ------------------ | -------------------- | --------------------------------------------- |
| Backend API        | Render (Web Service) | Deploys from `main` branch of this repo       |
| PostgreSQL DB      | Render (PostgreSQL)  | Managed database with automatic backups       |
| Media File Storage | AWS S3 Bucket        | Used for candidate profile images and resumes |

### 🔐 Environment Variables

- These are set in the Render Dashboard:

```bash
DEBUG=False
SECRET_KEY=your-production-secret
DATABASE_URL=provided-by-render
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket-name
AWS_S3_REGION_NAME=your-aws-region
```

## 🗂️ Media File Handling

- Uploaded media files (e.g., profile photos) are stored in an AWS S3 bucket using django-storages. Ensure the following settings are present in settings.py:

```bash
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
```

## 🚧 Roadmap

- Email notifications
- Forgot password email reset flow
- Admin dashboard metrics
- Audit log

## Contact

- For questions about this project or more information, contact Ginabeth Russell • ginabeth@tinysitelab.com

## 📝 License

- This code is proprietary and owned by Tiny Site Lab.
- All rights are reserved. Unauthorized use, distribution, or modification is strictly prohibited.

- For licensing or partnership inquiries, contact ginabeth@tinysitelab.com.
