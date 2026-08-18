import mysql.connector

from config import Config


def get_connection():

    connection = mysql.connector.connect(

        host=Config.MYSQL_HOST,

        user=Config.MYSQL_USER,

        password=Config.MYSQL_PASSWORD,

        database=Config.MYSQL_DATABASE,

        port=Config.MYSQL_PORT

    )

    return connection


def save_allocation(
    user_id,
    activity,
    requested_bandwidth,
    allocated_bandwidth,
    utility,
    fairness_index
):

    connection = None

    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor()


        query = """

        INSERT INTO allocation_history

        (
            user_id,
            activity,
            requested_bandwidth,
            allocated_bandwidth,
            utility,
            fairness_index
        )

        VALUES (%s, %s, %s, %s, %s, %s)

        """


        values = (

            user_id,

            activity,

            requested_bandwidth,

            allocated_bandwidth,

            utility,

            fairness_index

        )


        cursor.execute(
            query,
            values
        )


        connection.commit()


    finally:

        if cursor:

            cursor.close()

        if connection:

            connection.close()