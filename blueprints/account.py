from flask import Blueprint, g, request

# maybe g is not the adequate place to store user_id, but it may work

def return_account_blueprint():
    account_bp = Blueprint("account", __name__, url_prefix="/<username>")

    from flask import g, request, abort

    @account_bp.before_request
    def load_user():
        username = request.view_args.get("username") or "demo"

        if not username:
            abort(404)  # or redirect somewhere sensible
        g.user_id = username

    return account_bp