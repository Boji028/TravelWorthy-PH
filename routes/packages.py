"""Package routes for tour listing, details, and visa information."""
from typing import Union, Dict, Any
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app import db, limiter
from models.package import TourPackage
from models.country import Country
from models.continent import Continent
from models.visa import VisaCountry

packages_bp = Blueprint('packages', __name__)


@packages_bp.route('/')
def list_packages() -> Union[str, object]:
    """List tour packages with filtering options.
    
    Query parameters:
        - destination: Filter by destination name
        - country_id: Filter by country
        - continent_id: Filter by continent
        - duration: Filter by duration days
        - guests: Filter by minimum available slots
        - page: Pagination page number
    """
    destination: str = request.args.get('destination', '')
    country_id: int = request.args.get('country_id', type=int)
    continent_id: int = request.args.get('continent_id', type=int)

    query = TourPackage.query.filter_by(is_active=True)

    if country_id:
        query = query.filter_by(country_id=country_id)
    elif continent_id:
        # Use subquery instead of Python loop to avoid N+1
        query = query.filter(
            TourPackage.country_id.in_(
                db.session.query(Country.id)
                .filter_by(continent_id=continent_id, is_active=True)
            )
        )

    if destination:
        query = query.filter(TourPackage.destination.ilike(f'%{destination}%'))

    duration: int = request.args.get('duration', type=int)
    guests: int = request.args.get('guests', type=int)

    if duration:
        query = query.filter(TourPackage.duration_days == duration)
    if guests:
        query = query.filter(TourPackage.available_slots >= guests)

    page: int = request.args.get('page', 1, type=int)
    packages = query.order_by(TourPackage.created_at.desc()).paginate(
        page=page, per_page=9, error_out=False
    )

    # Load related continent/country data to prevent N+1 queries
    continents = (
        Continent.query
        .filter_by(is_active=True)
        .order_by(Continent.name)
        .all()
    )
    active_continent = db.session.get(Continent, continent_id) if continent_id else None
    active_country = db.session.get(Country, country_id) if country_id else None

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('packages/list_ajax.html', packages=packages.items)

    return render_template('packages/list.html',
                           packages=packages.items,
                           pagination=packages,
                           continents=continents,
                           active_continent=active_continent,
                           active_country=active_country)


@packages_bp.route('/<int:package_id>')
def package_detail(package_id: int) -> str:
    """Display detailed view of a tour package.
    
    Args:
        package_id: ID of the package
    """
    package = db.get_or_404(TourPackage, package_id)
    return render_template('packages/detail.html', package=package)


@packages_bp.route('/autocomplete')
@limiter.limit("60 per minute")
def autocomplete() -> str:
    """Autocomplete endpoint for destination and country search.
    
    Rate limited to prevent keystroke abuse.
    """
    q: str = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])

    results: list = []

    # Query for package destinations
    packages = TourPackage.query.filter(
        TourPackage.is_active == True,
        TourPackage.destination.ilike(f'%{q}%')
    ).limit(5).all()

    for p in packages:
        if p.destination not in [r['name'] for r in results]:
            results.append({'name': p.destination})

    # Query for countries
    countries = Country.query.filter(
        Country.is_active == True,
        Country.name.ilike(f'%{q}%')
    ).limit(3).all()

    for c in countries:
        if c.name not in [r['name'] for r in results]:
            results.append({'name': c.name})

    return jsonify(results[:6])


@packages_bp.route('/visa')
def visa() -> str:
    """Display visa requirements by country."""
    countries = VisaCountry.query.filter_by(is_active=True).order_by(VisaCountry.country_name).all()
    return render_template('packages/visa.html', countries=countries)


@packages_bp.route('/visa/country/<int:visa_id>/requirements')
def visa_requirements(visa_id: int) -> str:
    """Display visa requirements for a specific country.
    
    Args:
        visa_id: ID of the visa country record
    """
    country = db.get_or_404(VisaCountry, visa_id)
    return jsonify({
        'id': country.id,
        'name': country.country_name,
        'flag_emoji': country.flag_emoji or '',
        'requirements': country.requirements or ''
    })
