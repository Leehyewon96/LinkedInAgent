# LinkedIn API

import requests
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")


def get_valid_token() -> str:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")

    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code == 401:
        print("토큰 만료 — 갱신 중...")
        token = refresh_access_token()

    return token


def refresh_access_token() -> str:
    response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.getenv("LINKEDIN_REFRESH_TOKEN"),
            "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
            "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
        }
    )
    data = response.json()
    new_token = data["access_token"]
    _update_env("LINKEDIN_ACCESS_TOKEN", new_token)
    return new_token


def get_profile_id(token: str) -> str:
    # r = requests.get(
    #     "https://api.linkedin.com/v2/me",
    #     headers={"Authorization": f"Bearer {token}"}
    # )
    # return r.json()["id"]
    return "833153287"


def post_to_linkedin(text: str, source_link:
    str = None,
    title: str = None,
    description: str = None,
    dry_run: bool = True
) -> dict:
    if dry_run:
        print("[DRY RUN] 실제 게시 안됨")
        print("\n" + "="*50)
        print(text)
        print("="*50)
        return {"dry_run": True}

    token = get_valid_token()

    # sub 값 직접 가져오기
    r = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"}
    )
    sub = r.json()["sub"]  # 8b0NX-H2KJ

    # 신규 REST API 사용
    response = requests.post(
        "https://api.linkedin.com/rest/posts",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202504",
        },
        json={
            "author": f"urn:li:person:{sub}",
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "content": {                          # ← 링크 카드 추가
                "article": {
                "source": source_link,        # 출처 URL
                "title": title,               # 카드 제목
                "description": description    # 카드 설명
                }
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }
    )

    if response.status_code == 201:
        post_id = response.headers.get("x-restli-id")
        print(f"게시 성공! post_id: {post_id}")
        return {"post_id": post_id, "status": "published"}
    else:
        raise Exception(f"게시 실패: {response.status_code} {response.text}")


def _update_env(key: str, value: str):
    with open(Path(__file__).parent.parent / ".env", "r") as f:
        lines = f.readlines()
    with open(Path(__file__).parent.parent / ".env", "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
            else:
                f.write(line)