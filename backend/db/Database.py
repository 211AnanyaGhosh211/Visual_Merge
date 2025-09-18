import mysql.connector
from flask import Flask, request, jsonify, Blueprint
from .db import db_config

class DBUtil:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(**db_config)
            self.cursor = self.conn.cursor()
            print("Connected to the database")
        except mysql.connector.Error as err:
            print(f"Error: {err}")


app = Flask(__name__)
db_util = DBUtil()
database_bp = Blueprint('database_bp', __name__)


def is_valid_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


@database_bp.route('/del_employee', methods=['DELETE'])
def del_employee():
    data = request.get_json()
    required_fields = ['employee_id']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        query = "DELETE FROM EmployeeInfo.Registered_Employees WHERE EmployeeID = %s"
        db_util.cursor.execute(query, (data['employee_id'],))
        db_util.conn.commit()

        if db_util.cursor.rowcount == 0:
            return jsonify({"error": "Employee records not found"}), 404

        return jsonify({"message": "Employee records deleted successfully"})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500


@database_bp.route('/get_camera', methods=['GET'])
def get_camera():
    camera_id = is_valid_int(request.args.get('camera_id'))
    if camera_id is None:
        return jsonify({"error": "Invalid camera_id"}), 400
    try:
        query = "SELECT * FROM EmployeeInfo.Camera WHERE Camera_id = %s"
        db_util.cursor.execute(query, (camera_id,))
        result = db_util.cursor.fetchone()
        return jsonify(result) if result else jsonify({"error": "Camera not found"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@database_bp.route('/set_camera', methods=['POST'])
def set_camera():
    data = request.get_json()
    required_fields = ['camera_id', 'camera_name', 'zone_name',
                       'ip_address', 'streaming_url', 'playback_url']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        query = "INSERT INTO EmployeeInfo.Camera (Camera_id,Camera_name, Zone_name, IP_address, Streaming_URL, Playback_URL) VALUES (%s, %s, %s, %s, %s, %s)"
        db_util.cursor.execute(query, (data['camera_id'], data['camera_name'], data['zone_name'],
                               data['ip_address'], data['streaming_url'], data['playback_url']))
        db_util.conn.commit()
        return jsonify({"message": "Camera inserted successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@database_bp.route('/del_camera', methods=['DELETE'])
def del_camera():
    data = request.get_json()
    required_fields = ['camera_id']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        query = "DELETE FROM EmployeeInfo.Camera WHERE Camera_id = %s"
        db_util.cursor.execute(query, (data['camera_id'],))
        db_util.conn.commit()

        if db_util.cursor.rowcount == 0:
            return jsonify({"error": "Camera not found"}), 404

        return jsonify({"message": "Camera deleted successfully"})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500

@database_bp.route('/get_model', methods=['GET'])
def get_model():
    model_id = is_valid_int(request.args.get('model_id'))
    if model_id is None:
        return jsonify({"error": "Invalid model_id"}), 400
    try:
        query = "SELECT * FROM EmployeeInfo.Models WHERE Model_ID = %s"
        db_util.cursor.execute(query, (model_id,))
        result = db_util.cursor.fetchone()
        return jsonify(result) if result else jsonify({"error": "Model not found"}), 404
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


@database_bp.route('/set_model', methods=['POST'])
def set_model():
    data = request.get_json()
    if not all(field in data for field in ['model_id', 'model_name', 'model_use']):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        query = "INSERT INTO EmployeeInfo.Models (Model_id, Modelname, Model_Use) VALUES (%s, %s, %s)"
        db_util.cursor.execute(
            query, (data['model_id'], data['model_name'], data['model_use']))
        db_util.conn.commit()
        return jsonify({"message": "Model inserted successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@database_bp.route('/del_model', methods=['DELETE'])
def del_model():
    data = request.get_json()
    required_fields = ['model_id']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        query = "DELETE FROM EmployeeInfo.Models WHERE Model_ID = %s"
        db_util.cursor.execute(query, (data['Model_id'],))
        db_util.conn.commit()

        if db_util.cursor.rowcount == 0:
            return jsonify({"error": "Model not found"}), 404

        return jsonify({"message": "Model deleted successfully"})
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": str(err)}), 500

@database_bp.route('/link_camera_model', methods=['POST'])
def link_camera_model():
    data = request.get_json()
    model_id = is_valid_int(data.get('model_id'))
    camera_id = is_valid_int(data.get('camera_id'))
    if model_id is None or camera_id is None:
        return jsonify({"error": "Invalid model_id or camera_id"}), 400
    try:
        query = "INSERT INTO EmployeeInfo.Camera_Model (Model_ID, Camera_id) VALUES (%s, %s)"
        db_util.cursor.execute(query, (model_id, camera_id))
        db_util.conn.commit()
        return jsonify({"message": "Camera and Model linked successfully"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500


if __name__ == '__main__':
    app.register_blueprint(database_bp, url_prefix='/api')
    app.run(debug=True)
