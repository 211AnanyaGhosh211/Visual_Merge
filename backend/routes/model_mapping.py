from flask import Blueprint, jsonify, request
import mysql.connector
from db.db import db_util

model_mapping_bp = Blueprint('model_mapping', __name__, url_prefix='/api/model_mapping')

def is_valid_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None




@model_mapping_bp.route('/get_model', methods=['GET'])
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


@model_mapping_bp.route('/set_model', methods=['POST'])
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

@model_mapping_bp.route('/del_model', methods=['DELETE'])
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

@model_mapping_bp.route('/link_camera_model', methods=['POST'])
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