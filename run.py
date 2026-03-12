import os
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

# Create Flask app
app = create_app()

# Ensure database tables exist and default admin is created
with app.app_context():
    db.create_all()

    # Create default admin if none exists
    if not User.query.filter_by(role="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# Run the app (for local testing)
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # required for Render
        port=int(os.environ.get("PORT", 5000)),
        debug=True       # remove debug=True for production
    )