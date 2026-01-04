import csv
import io
from flask import Blueprint, render_template, request, Response, flash

from app.models.trial import SearchParams, VALID_PHASES, VALID_STATUSES
from app.services.clinical_trials import ClinicalTrialsService

search_bp = Blueprint('search', __name__)
service = ClinicalTrialsService()


@search_bp.route('/')
def index():
    """Render the search form."""
    return render_template(
        'search.html',
        phases=VALID_PHASES,
        statuses=VALID_STATUSES
    )


@search_bp.route('/search')
def search():
    """Execute search and render results table."""
    compound = request.args.get('compound', '').strip()
    condition = request.args.get('condition', '').strip()
    phases = request.args.getlist('phases')
    statuses = request.args.getlist('statuses')

    # Require at least one search criterion
    if not any([compound, condition, phases, statuses]):
        flash('Please enter at least one search criterion.', 'warning')
        return render_template(
            'search.html',
            phases=VALID_PHASES,
            statuses=VALID_STATUSES
        )

    params = SearchParams(
        compound=compound or None,
        condition=condition or None,
        phases=phases or None,
        statuses=statuses or None
    )

    try:
        result = service.fetch_all(params)
    except Exception as e:
        flash(f'Error fetching results: {str(e)}', 'danger')
        return render_template(
            'search.html',
            phases=VALID_PHASES,
            statuses=VALID_STATUSES
        )

    return render_template(
        'results.html',
        trials=result.trials,
        total_count=result.total_count,
        truncated=result.truncated,
        params=params,
        phases=VALID_PHASES,
        statuses=VALID_STATUSES
    )


@search_bp.route('/export')
def export():
    """Stream CSV download of search results."""
    compound = request.args.get('compound', '').strip()
    condition = request.args.get('condition', '').strip()
    phases = request.args.getlist('phases')
    statuses = request.args.getlist('statuses')

    params = SearchParams(
        compound=compound or None,
        condition=condition or None,
        phases=phases or None,
        statuses=statuses or None
    )

    result = service.fetch_all(params)

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'NCT ID', 'Title', 'Phase', 'Status', 'Sponsor', 'Conditions', 'Interventions'
    ])

    # Data rows
    for trial in result.trials:
        writer.writerow([
            trial.nct_id,
            trial.title,
            trial.phase,
            trial.status,
            trial.sponsor,
            '; '.join(trial.conditions),
            '; '.join(trial.interventions)
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=clinical_trials.csv'}
    )
