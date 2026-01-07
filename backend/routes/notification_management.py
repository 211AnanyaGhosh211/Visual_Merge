from flask import Blueprint, jsonify
import mysql.connector
import logging
from datetime import datetime, timedelta
from db.db import db_config

notification_management_bp = Blueprint('notification_management', __name__, url_prefix='/api/notification_management')


def get_notifications():
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        sql = """
        SELECT Exception_Type, Username, time_occurred
        FROM EmployeeInfo.Exception_Logs
        ORDER BY time_occurred DESC 
        LIMIT 12
        """
        cursor.execute(sql)
        notifications = []

        for row in cursor.fetchall():
            # Type cast to avoid linter issues
            notification: dict = dict(row)  # type: ignore

            # # Convert BLOB to base64 if image exists
            # if 'Incident_image' in notification and notification['Incident_image']:
            #     img_data = notification['Incident_image']
            #     if isinstance(img_data, bytes):
            #         notification['image_base64'] = base64.b64encode(img_data).decode('utf-8')
            # Time formatting remains the same
            if 'time_occurred' in notification:
                time_occurred = notification['time_occurred']
                if isinstance(time_occurred, str):
                    time_occurred = datetime.strptime(
                        time_occurred, '%Y-%m-%d %H:%M:%S')
                elif not isinstance(time_occurred, datetime):
                    time_occurred = datetime.now()

                time_diff = datetime.now() - time_occurred

                if time_diff < timedelta(minutes=1):
                    notification['time_ago'] = "Just now"
                elif time_diff < timedelta(hours=1):
                    minutes = int(time_diff.seconds / 60)
                    notification['time_ago'] = f"{minutes} mins ago"
                elif time_diff < timedelta(days=1):
                    hours = int(time_diff.seconds / 3600)
                    notification['time_ago'] = f"{hours} hours ago"
                else:
                    days = time_diff.days
                    notification['time_ago'] = f"{days} days ago"

            notifications.append(notification)

        return notifications
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@notification_management_bp.route('/notifications', methods=['GET'])
def get_notifications_api():
    try:
        notifications = get_notifications()
        return jsonify(notifications)
    except Exception as e:
        logging.error(f"Error in notifications route: {e}")
        return jsonify({"error": str(e)}), 500


