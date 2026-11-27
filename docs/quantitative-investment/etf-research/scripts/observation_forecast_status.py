"""Read verified fold and forecast progress across the independent research archive."""
from datetime import date

from observation_labels import EVIDENCE_ERRORS, label_window
from seal_observation_forecasts import LOG, compare_model, verify_forecast
from train_observation_models import describe_fold, status as trained_status, verify_model
from etf_research.observation_decision_receipt import DECISIONS, deadline
from etf_research.observation_experiment import VARIANTS, feature_vector
from etf_research.policy_events import instant
from etf_research.publication import inside, read


def model_progress(root, store, origin, observed):
    try:
        row=trained_status(root,store,observed)
        if row['studyOrigin']!=origin:
            raise ValueError('Models use a different study origin')
    except EVIDENCE_ERRORS:
        row=dict(describe_fold(origin,observed),status='model_unverified')
    if row['status']=='fold_active':
        if 'modelReceipt' not in row:
            row['status']='awaiting_model'
        else:
            row['status']='model_verified' if any(
                x['status']=='fitted' for x in row['comparisons'].values()) else 'insufficient_training'
    return row


def forecast_row(root,store,day,observed,origin,decision,*,details=False,models=None):
    shape=dict(status='not_scheduled',fold=None,deadline=None,sessions=[],
               readyAt=None,latest=None,attempts=[],sealedVariants=[])
    if not decision['scheduledAt']:
        return dict(shape,status='calendar_unverified') if decision['status']=='calendar_unknown' else shape
    cutoff=deadline(day)
    if origin and instant(origin['archiveVerifiedAt'])>cutoff:
        origin=None
    plan=describe_fold(origin,cutoff)
    models={} if models is None else models
    if not plan['fold']:
        return dict(shape,status=plan['status'])
    shape.update(fold=plan['fold'])
    try:
        window=label_window(root,day)
    except EVIDENCE_ERRORS:
        return dict(shape,status='calendar_unverified')
    shape['sessions']=[str(d) for d in window.sessions]
    if window.last>=date.fromisoformat(plan['fold']['end']):
        return dict(shape,status='holding_window_crosses_fold')
    shape['deadline']=cutoff.isoformat()

    attempts=[]
    for folder in sorted((root/LOG/str(day)).glob('*')):
        if not folder.is_dir() or folder.is_symlink():
            continue
        path=folder/'receipt.json'
        try:
            if not path.is_file():
                attempts.append(dict(id=folder.name,status='pending_archive' if observed<cutoff else 'incomplete'))
                continue
            if instant(read(path)['forecastSealedAt'])>observed:
                continue
            receipt,packet=verify_forecast(root,store,folder,observed=observed)
            if packet['studyOrigin']!=origin or packet['fold']!=shape['fold']:
                raise ValueError('Forecast belongs to another study or fold')
            if packet['sessions'] and packet['sessions']!=shape['sessions']:
                raise ValueError('Forecast holds a different set of sessions')
            status=receipt['status']
            record=dict(id=folder.name,status=status,sealedAt=receipt['forecastSealedAt'],
                        archiveSha256=receipt['archiveSha256'],reason=packet['reason'],sealedVariants=[])
            if status=='sealed_predictions':
                item=decision['latest']
                bound=packet['decision']
                if (decision['status']!='eligible_inputs' or
                        bound['path']!=f'{DECISIONS}/{day}/{item["id"]}' or
                        bound['receiptSha256']!=item['receiptSha256'] or
                        bound['archiveSha256']!=item['archiveSha256'] or bound['sealedAt']!=item['archivedAt']):
                    raise ValueError('Forecast decision archive cannot be matched')
                model=packet['model']
                key=(model['path'],model['archiveSha256'])
                if key not in models:
                    models[key]=verify_model(root,store,inside(root,model['path']),observed=observed)
                proof,fit=models[key]
                if (proof['archiveSha256']!=model['archiveSha256'] or proof['modelSealedAt']!=model['sealedAt']
                        or instant(proof['modelSealedAt'])>instant(packet['computedAt'])
                        or fit['cohort']['studyOrigin']!=origin or fit['cohort']['fold']!=shape['fold']):
                    raise ValueError('Forecast model archive cannot be matched')
                cells=read(inside(root,bound['path'])/'records/inputs.json')['cells']
                for variant,prediction in packet['comparisons'].items():
                    if prediction['status']!='predicted':
                        continue
                    trained=fit['comparisons'][variant]
                    values=feature_vector(cells,VARIANTS[variant],window,sealed=instant(bound['sealedAt']))
                    if (values is None or prediction['modelSha256']!=trained['modelSha256'] or
                            compare_model(trained,variant,values)!={name:prediction[name] for name in ('baseline','expanded')}):
                        raise ValueError('Forecast scores do not reproduce')
                    record['sealedVariants'].append(variant)
                if not record['sealedVariants']:
                    raise ValueError('No verified comparisons in the sealed forecast')
            if details:
                record['comparisons']=packet['comparisons'] if status=='sealed_predictions' else {
                    key:{name:value for name,value in stat.items() if name not in ('baseline','expanded')}
                    for key,stat in packet['comparisons'].items()}
                record['modelArchiveSha256']=packet['model']['archiveSha256'] if packet['model'] else None
            attempts.append(record)
        except EVIDENCE_ERRORS:
            attempts.append(dict(id=folder.name,status='unverified'))

    verified=[row for row in attempts if 'sealedAt' in row]
    first=min((row for row in verified if row['status']=='sealed_predictions'),
              key=lambda row:instant(row['sealedAt']),default=None)
    latest=first or max(verified,key=lambda row:instant(row['sealedAt']),default=None)
    if latest is None and attempts:
        latest=attempts[-1]
    return dict(shape,status=latest['status'] if latest else 'pending' if observed<cutoff else 'missing',
                latest=latest,attempts=attempts,readyAt=first['sealedAt'] if first else None,
                sealedVariants=first['sealedVariants'] if first else [])


def forecast_counts(rows, observed):
    due=[row for row in rows if row['deadline'] and instant(row['deadline'])<=observed]
    sealed=sum(row['status']=='sealed_predictions' for row in due)
    per_variant={name:sum(name in row['sealedVariants'] for row in due)
                 for name in VARIANTS if name!='baseline'}
    return dict(due=len(due),sealedDays=sealed,gaps=len(due)-sealed,sealedPairs=per_variant,
                unknownCalendar=sum(row['status']=='calendar_unverified' for row in rows))
