from flask import Blueprint, render_template
from services.recommendation_engine import RecommendationEngine

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/insights')
def index():
    insights = RecommendationEngine.get_insights()
    recommendations = RecommendationEngine.get_customer_recommendations()
    return render_template('insights.html', insights=insights, recommendations=recommendations)
