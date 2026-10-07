import asyncio
import sys
if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def test_signup(client):
    """
    - Test sign up is successful - 201
    - Test sign up with duplicate sign up is unsuccessful with status code - 409
    """
    response=client.post(
        '/signup',
        json={
            "email":"test@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==201

    response=client.post(
        '/signup',
        json={
            "email":"test@example.com",
            "password":"stringst"
        }
    )

    assert response.status_code==409