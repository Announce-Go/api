"""OpenAPI/Swagger 그룹 설정"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

if TYPE_CHECKING:
    from fastapi import APIRouter


@dataclass
class OpenAPIGroup:
    """OpenAPI 그룹 정의"""

    name: str
    display_name: str
    description: str
    routers: list[tuple[APIRouter, str]]  # (router, prefix)


def get_openapi_groups() -> list[OpenAPIGroup]:
    """OpenAPI 그룹 목록 반환"""
    from app.routers import (
        auth_router,
        signup_router,
        files_router,
        # Admin
        admin_members_router,
        admin_place_rank_router,
        admin_cafe_rank_router,
        admin_blog_rank_router,
        admin_dashboard_router,
        admin_blog_posting_router,
        admin_press_router,
        admin_cafe_infiltration_router,
        # Agency
        agency_common_router,
        agency_place_rank_router,
        agency_cafe_rank_router,
        agency_blog_rank_router,
        agency_dashboard_router,
        agency_blog_posting_router,
        agency_press_router,
        agency_cafe_infiltration_router,
        # Advertiser
        advertiser_common_router,
        advertiser_place_rank_router,
        advertiser_cafe_rank_router,
        advertiser_blog_rank_router,
        advertiser_dashboard_router,
        advertiser_blog_posting_router,
        advertiser_press_router,
        advertiser_cafe_infiltration_router,
    )

    return [
        OpenAPIGroup(
            name="common",
            display_name="Common (공통)",
            description="공통 API (인증, 회원가입, 파일, 헬스체크)",
            routers=[
                (auth_router, "/api/v1"),
                (signup_router, "/api/v1"),
                (files_router, "/api/v1"),
            ],
        ),
        OpenAPIGroup(
            name="admin",
            display_name="Admin (관리자)",
            description="관리자용 API (회원관리, 순위추적, 대시보드, 작업기록 관리)",
            routers=[
                (admin_members_router, "/api/v1"),
                (admin_place_rank_router, "/api/v1"),
                (admin_cafe_rank_router, "/api/v1"),
                (admin_blog_rank_router, "/api/v1"),
                (admin_dashboard_router, "/api/v1"),
                (admin_blog_posting_router, "/api/v1"),
                (admin_press_router, "/api/v1"),
                (admin_cafe_infiltration_router, "/api/v1"),
            ],
        ),
        OpenAPIGroup(
            name="agency",
            display_name="Agency (광고업체)",
            description="광고 업체용 API (순위추적 등록/조회, 대시보드, 작업기록)",
            routers=[
                (agency_common_router, "/api/v1"),
                (agency_place_rank_router, "/api/v1"),
                (agency_cafe_rank_router, "/api/v1"),
                (agency_blog_rank_router, "/api/v1"),
                (agency_dashboard_router, "/api/v1"),
                (agency_blog_posting_router, "/api/v1"),
                (agency_press_router, "/api/v1"),
                (agency_cafe_infiltration_router, "/api/v1"),
            ],
        ),
        OpenAPIGroup(
            name="advertiser",
            display_name="Advertiser (광고주)",
            description="광고주용 API (순위추적 조회, 대시보드, 작업기록)",
            routers=[
                (advertiser_common_router, "/api/v1"),
                (advertiser_place_rank_router, "/api/v1"),
                (advertiser_cafe_rank_router, "/api/v1"),
                (advertiser_blog_rank_router, "/api/v1"),
                (advertiser_dashboard_router, "/api/v1"),
                (advertiser_blog_posting_router, "/api/v1"),
                (advertiser_press_router, "/api/v1"),
                (advertiser_cafe_infiltration_router, "/api/v1"),
            ],
        ),
    ]


def setup_openapi(
    app: FastAPI,
    docs_path: str = "/docs",
    api_docs_prefix: str = "/api-docs",
) -> None:
    """
    Swagger 그룹을 설정합니다.

    Args:
        app: 메인 FastAPI 앱
        docs_path: 통합 Swagger UI 경로
        api_docs_prefix: 그룹별 OpenAPI 스펙 경로 prefix
    """
    groups = get_openapi_groups()
    swagger_urls = []

    for group in groups:
        # 그룹별 서브 앱 생성
        sub_app = FastAPI(
            title=f"Announce-Go API - {group.display_name}",
            description=group.description,
            version="0.1.0",
        )

        # 라우터 등록
        for router, prefix in group.routers:
            sub_app.include_router(router, prefix=prefix)

        # OpenAPI 스키마 커스텀 (servers 제거 → 현재 페이지 기준으로 요청)
        def custom_openapi(app: FastAPI = sub_app, grp: OpenAPIGroup = group):
            if app.openapi_schema:
                return app.openapi_schema
            from fastapi.openapi.utils import get_openapi

            schema = get_openapi(
                title=f"Announce-Go API - {grp.display_name}",
                version="0.1.0",
                description=grp.description,
                routes=app.routes,
            )
            schema.pop("servers", None)
            app.openapi_schema = schema
            return schema

        sub_app.openapi = custom_openapi

        # 메인 앱에 마운트
        app.mount(f"{api_docs_prefix}/{group.name}", sub_app)

        # Swagger URL 목록에 추가
        swagger_urls.append(
            {"url": f"{api_docs_prefix}/{group.name}/openapi.json", "name": group.display_name}
        )

    # 통합 Swagger UI 엔드포인트 등록
    @app.get(docs_path, response_class=HTMLResponse, include_in_schema=False)
    async def swagger_ui_with_dropdown() -> str:
        """드롭다운으로 API 그룹을 선택할 수 있는 Swagger UI"""
        urls_json = str(swagger_urls).replace("'", '"')
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Announce-Go API - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        html {{ box-sizing: border-box; overflow-y: scroll; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin: 0; background: #fafafa; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                urls: {urls_json},
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
</body>
</html>
"""
