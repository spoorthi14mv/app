from flask import Blueprint, render_template
from flask_login import login_required
from services.recommendation_engine import RecommendationEngine

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/insights')
@login_required
def index():
    insights = RecommendationEngine.get_insights()
    recommendations = RecommendationEngine.get_customer_recommendations()
    return render_template('insights.html', insights=insights, recommendations=recommendations)
