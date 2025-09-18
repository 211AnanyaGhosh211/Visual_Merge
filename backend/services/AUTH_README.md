# Authentication API Documentation

## Overview

This module contains all authentication-related APIs for the Visual Merge application. The authentication system is completely separate from the database operations and other application logic.

## Files

- `auth.py` - Main authentication module with all auth-related endpoints
- `test_login_api.py` - Test script for authentication APIs

## API Endpoints

### 1. Login

**Endpoint:** `POST /api/login`

**Description:** Authenticates users against the MySQL database using EmployeeID and password.

**Request Body:**

```json
{
  "employeeId": "7",
  "password": "plaintext_password"
}
```

**Response (Success):**

```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "employeeId": "7",
    "employeeName": "Avijit Patra",
    "loginTime": "2025-01-11 10:30:00"
  }
}
```

**Response (Error - Employee ID not found):**

```json
{
  "success": false,
  "error": "Employee ID '999' is not present in the database"
}
```

**Response (Error - Invalid password):**

```json
{
  "success": false,
  "error": "Invalid password"
}
```

### 2. Logout

**Endpoint:** `POST /api/logout`

**Description:** Handles user logout (currently frontend-only, but can be extended for server-side session management).

**Response:**

```json
{
  "success": true,
  "message": "Logout successful"
}
```

### 3. Verify Token

**Endpoint:** `POST /api/verify-token`

**Description:** Token verification endpoint for future JWT/session token validation.

**Request Body:**

```json
{
  "token": "your_token_here"
}
```

## Security Features

1. **SHA2 Password Hashing**: All passwords are hashed using SHA-256
2. **Input Validation**: Both client-side and server-side validation
3. **SQL Injection Protection**: Uses parameterized queries
4. **Error Handling**: Comprehensive error responses

## Database Requirements

The authentication system expects a MySQL table with this structure:

```sql
CREATE TABLE Registered_Employees (
    EmployeeName VARCHAR(255),
    EmployeeID VARCHAR(50) PRIMARY KEY,
    Images VARCHAR(255),
    Password VARCHAR(255)  -- SHA2 hashed passwords
);
```

## Usage

1. **Start the Flask server:**

   ```bash
   python app.py
   ```

2. **Test the API:**

   ```bash
   python test_login_api.py
   ```

3. **Frontend Integration:**
   The frontend (React) calls the login endpoint and handles the response.

## Configuration

Update the database connection details in `auth.py`:

```python
auth_db = AuthDBUtil(
    host='localhost',
    user='root',
    password='12345',
    database='EmployeeInfo'
)
```

## Error Codes

- `400` - Bad Request (missing fields, invalid input)
- `401` - Unauthorized (invalid credentials)
- `500` - Internal Server Error (database errors, unexpected errors)
