
from flask import request, jsonify, Blueprint
import mysql.connector
from db.db import db_util

camera_management_bp = Blueprint('camera_management', __name__, url_prefix='/api/camera_management')


def is_valid_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

@camera_management_bp.route('/cameras', methods=['GET'])
def get_cameras():
    try:
        # Check if database connection is alive
        if not db_util.conn.is_connected():
            db_util.conn.reconnect()
        
        query = "SELECT * FROM EmployeeInfo.Camera"
        db_util.cursor.execute(query)
        results = db_util.cursor.fetchall()
        
        # Convert to list of dictionaries for better JSON serialization
        columns = [desc[0] for desc in db_util.cursor.description]
        cameras = []
        for row in results:
            camera_dict = dict(zip(columns, row))
            cameras.append(camera_dict)
        
        print(f"Found {len(cameras)} cameras")
        return jsonify(cameras)
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": str(e)}), 500



@camera_management_bp.route('/get_camera', methods=['GET'])
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

@camera_management_bp.route('/set_camera', methods=['POST'])
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


@camera_management_bp.route('/del_camera', methods=['DELETE'])
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
