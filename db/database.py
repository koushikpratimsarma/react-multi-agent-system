import psycopg

from config import POSTGRES_URI



def save_message(
    thread_id: str,
    role: str,
    content: str,
    agent_name: str = None,
):
    with psycopg.connect(POSTGRES_URI) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_messages
                (thread_id, role, agent_name, content)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    thread_id,
                    role,
                    agent_name,
                    content,
                ),
            )

        conn.commit()


async def async_save_message(
    thread_id: str,
    role: str,
    content: str,
    agent_name: str = None,
):
    async with await psycopg.AsyncConnection.connect(
        POSTGRES_URI
    ) as conn:

        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO chat_messages
                (thread_id, role, agent_name, content)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    thread_id,
                    role,
                    agent_name,
                    content,
                ),
            )

        await conn.commit()

async def async_save_tool_call(
    thread_id: str,
    agent_name: str,
    tool_name: str,
    tool_input: str,
    tool_output: str,
):
    async with await psycopg.AsyncConnection.connect(
        POSTGRES_URI
    ) as conn:

        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO tool_calls
                (thread_id, agent_name, tool_name, tool_input, tool_output)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    thread_id,
                    agent_name,
                    tool_name,
                    tool_input,
                    tool_output,
                ),
            )

        await conn.commit()