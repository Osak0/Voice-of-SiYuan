# Voice-of-SiYuan
A private campus forum for XJTUers (Xi'an Jiaotong University)

## About
Voice of SiYuan is a campus forum built with FastAPI, designed to facilitate discussions among XJTU students. This is currently at the MVP (Minimum Viable Product) stage.

## Features
- User registration and authentication (JWT-based)
- Create, read, update, and delete posts
- Comment on posts
- User profile management

## Tech Stack
- **Backend**: FastAPI
- **Authentication**: JWT with OAuth2
- **Password Hashing**: bcrypt

## Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Osak0/Voice-of-SiYuan.git
cd Voice-of-SiYuan
```

2. Create a virtual environment:
```bash
python -m venv venv1
```

3. Activate the virtual environment:
- On Windows:
  ```bash
  venv1\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source venv1/bin/activate
  ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

Start the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user profile

### Posts
- `GET /posts` - List all posts (with pagination)
- `GET /posts/{post_id}` - Get a specific post
- `POST /posts` - Create a new post (requires authentication)
- `PUT /posts/{post_id}` - Update a post (requires authentication)
- `DELETE /posts/{post_id}` - Delete a post (requires authentication)

### Comments
- `GET /posts/{post_id}/comments` - Get all comments for a post
- `POST /posts/{post_id}/comments` - Add a comment to a post (requires authentication)

## Development Status

This project is currently in MVP stage. The following features are implemented:
- ✅ User registration and authentication
- ✅ Post creation, viewing, updating, and deletion
- ✅ Comment system
- ✅ Basic authorization (users can only edit/delete their own posts)

## Future Enhancements
- Database integration (SQLite/PostgreSQL)
- File upload support for images
- User roles and permissions
- Post categories and tags
- Search functionality
- Like/upvote system
- Email verification

## Contributing
This is a private campus project for XJTU students. If you'd like to contribute, please reach out to the maintainers.

## License
See LICENSE file for details.
