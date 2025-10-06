from flask import Blueprint, jsonify, render_template
import mysql.connector
import logging
from db.db import get_db_connection

model_management_bp = Blueprint('model_management', __name__, url_prefix='/api/model_management')


@model_management_bp.route('/models', methods=['GET'])
def get_models():
    """Get all registered models."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM EmployeeInfo.Models")
        models = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(models)
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@model_management_bp.route('/model_management.html', methods=['GET'])
def model_management():
    """Display model configuration."""
    conn = get_db_connection()
    models = []
    if conn:
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM EmployeeInfo.Models")
            models = cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()
    return render_template('model_management.html', models=models)
