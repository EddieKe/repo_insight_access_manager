from flask import Flask, jsonify, request, abort, send_file
from flask_cors import CORS
from platform_client import (
    fetch_workspaces,
    fetch_code_repos,
    fetch_repo_access,
    fetch_teams,
    fetch_team_members,
    fetch_user_rights,
    register_repo,
    get_registered_repos,
    fetch_repo_members,
    fetch_user_repo_rights,
    reload_platform_config,
    cache
)
from excel_generator import export_access_to_excel
import os
import tempfile
from datetime import datetime
from settings_manager import (
    get_platform_config,
    save_platform_config
)

app = Flask(__name__)
CORS(app)

BASE = '/v1'   # changed prefix

# --- Helper ---
def _bool_param(name):
    val = request.args.get(name, 'false').lower()
    return val in ('1', 'true', 'yes')

# --- Workspaces (formerly Projects) ---
@app.route(f"{BASE}/workspaces", methods=["GET"])
def list_workspaces():
    """List all workspaces"""
    refresh = _bool_param('refresh')
    return jsonify(fetch_workspaces())

@app.route(f"{BASE}/workspaces/<string:ws_id>", methods=["GET"])
def workspace_detail(ws_id):
    workspaces = fetch_workspaces()
    ws = next((w for w in workspaces if w.get('id') == ws_id or w.get('name') == ws_id), None)
    if not ws:
        abort(404)
    return jsonify(ws)

@app.route(f"{BASE}/workspaces/<string:ws_id>/repos", methods=["GET"])
def list_repos(ws_id):
    return jsonify(fetch_code_repos(ws_id))

@app.route(f"{BASE}/workspaces/<string:ws_id>/teams", methods=["GET"])
def list_teams(ws_id):
    return jsonify(fetch_teams(ws_id))

# --- Repositories ---
@app.route(f"{BASE}/repos/<string:repo_id>/access", methods=["GET"])
def repo_access(repo_id):
    return jsonify(fetch_repo_access(repo_id))

@app.route(f"{BASE}/repos/<string:repo_id>/members", methods=["GET"])
def repo_members(repo_id):
    return jsonify(fetch_repo_members(repo_id))

@app.route(f"{BASE}/repos/<string:repo_id>/users/<string:descriptor>/rights", methods=["GET"])
def user_repo_rights(repo_id, descriptor):
    return jsonify(fetch_user_repo_rights(descriptor, repo_id))

# --- Teams & Users ---
@app.route(f"{BASE}/teams/<string:descriptor>/members", methods=["GET"])
def team_members(descriptor):
    return jsonify(fetch_team_members(descriptor))

@app.route(f"{BASE}/users/<string:descriptor>/rights", methods=["GET"])
def user_rights(descriptor):
    return jsonify(fetch_user_rights(descriptor))

# --- Registered repos ---
@app.route(f"{BASE}/registered-repos", methods=["POST"])
def register_repo_endpoint():
    data = request.get_json() or {}
    repo_id = data.get('repoId')
    if not repo_id:
        abort(400, description='repoId required')
    register_repo(repo_id)
    return jsonify({'status': 'registered', 'repoId': repo_id}), 201

@app.route(f"{BASE}/registered-repos", methods=["GET"])
def list_registered_repos():
    return jsonify(get_registered_repos())

# --- Export ---
@app.route(f"{BASE}/workspaces/<string:ws_id>/export-report", methods=["GET"])
def export_workspace_report(ws_id):
    workspaces = fetch_workspaces()
    workspace = next((w for w in workspaces if w.get('id') == ws_id or w.get('name') == ws_id), None)
    if not workspace:
        abort(404, description=f"Workspace {ws_id} not found")
    temp_dir = tempfile.gettempdir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{workspace['name']}_access_report_{timestamp}.xlsx"
    output_path = os.path.join(temp_dir, filename)
    export_access_to_excel(output_path, ws_id)
    return send_file(
        output_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

# --- Configuration ---
@app.route(f"{BASE}/config/platform", methods=["GET"])
def get_config():
    config = get_platform_config()
    if config.get("api_token"):
        config["api_token"] = "********"
    return jsonify(config)

@app.route(f"{BASE}/config/platform", methods=["POST"])
def save_config():
    data = request.get_json() or {}
    org_url = data.get('org_url')
    token = data.get('api_token')
    if not org_url or not token:
        return jsonify({"error": "org_url and api_token required"}), 400
    success = save_platform_config(org_url, token)
    if not success:
        return jsonify({"error": "Failed to save config"}), 500
    reload_platform_config()
    return jsonify({"status": "Configuration saved"})

# --- Cache ---
@app.route(f"{BASE}/cache/clear", methods=["POST"])
def clear_cache():
    cache.clear()
    return jsonify({"status": "Cache cleared"}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not Found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
