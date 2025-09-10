import mysql.connector
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, Blueprint

# Create authentication blueprint
auth_bp = Blueprint('auth_bp', __name__)


class AuthDBUtil:
    def __init__(self, host, user, password, database):
        try:
            self.conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.conn.cursor()
            print("Auth database connected successfully")
        except mysql.connector.Error as err:
            print(f"Auth database connection error: {err}")


# Initialize database connection for authentication
auth_db = AuthDBUtil(host='localhost', user='root',
                     password='12345', database='EmployeeInfo')


@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Login endpoint that authenticates users against the admins table
    Expects JSON payload: {"adminId": "1", "password": "plaintext_password"}
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response

    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'adminId' not in data or 'username' not in data or 'password' not in data:
            return jsonify({
                "success": False,
                "error": "Missing required fields: adminId, username and password"
            }), 400

        admin_id = data['adminId']
        username = data['username']
        password = data['password']

        # Validate input
        if not admin_id or not username or not password:
            return jsonify({
                "success": False,
                "error": "Admin ID, username and password cannot be empty"
            }), 400

        # Hash the provided password using SHA2 (SHA-256)
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        # Query database for admin
        query = """
        SELECT AdminID, Username, Password, Role 
        FROM EmployeeInfo.Admins 
        WHERE AdminID = %s AND Username = %s
        """

        auth_db.cursor.execute(query, (admin_id, username))
        result = auth_db.cursor.fetchone()

        if not result:
            return jsonify({
                "success": False,
                "error": f"Admin ID '{admin_id}' with username '{username}' is not present in the database"
            }), 401

        db_admin_id, db_username, db_password, role = result

        # Compare hashed passwords
        if hashed_password == db_password:
            return jsonify({
                "success": True,
                "message": "Login successful",
                "user": {
                    "adminId": db_admin_id,
                    "username": username,
                    "role": role,
                    "loginTime": str(datetime.now())
                }
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Invalid password"
            }), 401

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({
            "success": False,
            "error": "Database error occurred"
        }), 500
    except Exception as err:
        print(f"Unexpected error: {err}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred"
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout endpoint (for future use if needed)
    Currently handled on frontend, but can be extended for server-side session management
    """
    try:
        # For now, just return success
        # In the future, you can add server-side session management here
        return jsonify({
            "success": True,
            "message": "Logout successful"
        }), 200
    except Exception as err:
        print(f"Logout error: {err}")
        return jsonify({
            "success": False,
            "error": "Logout failed"
        }), 500


@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """
    Token verification endpoint (for future use)
    Can be used to verify JWT tokens or session tokens
    """
    try:
        data = request.get_json()

        if not data or 'token' not in data:
            return jsonify({
                "success": False,
                "error": "Token required"
            }), 400

        # For now, just return success
        # In the future, implement actual token verification
        return jsonify({
            "success": True,
            "message": "Token is valid"
        }), 200
    except Exception as err:
        print(f"Token verification error: {err}")
        return jsonify({
            "success": False,
            "error": "Token verification failed"
        }), 500


if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.run(debug=True)
