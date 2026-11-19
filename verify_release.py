"""Check aggregate outputs with standard library APIs; no participant input needed."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def read(path):
    return pd.read_csv(ROOT/path, float_precision='round_trip')


def main():
    manifest=json.loads((ROOT/'release_manifest.json').read_text(encoding='utf-8'))
    listed={item['path'] for item in manifest['files']}
    excluded_directories={'.git','__pycache__','.venv','outputs'}
    actual={path.relative_to(ROOT).as_posix() for path in ROOT.rglob('*')
            if path.is_file() and not (set(path.relative_to(ROOT).parts)&excluded_directories)}
    assert actual==listed|{'release_manifest.json'}, 'Release contains missing or unlisted files.'
    for item in manifest['files']:
        path=ROOT/item['path']
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual==item['sha256'], f"File changed: {item['path']}"
        if path.suffix=='.py':
            compile(path.read_text(encoding='utf-8-sig'),str(path),'exec')
    forbidden={'eid','subject_id','subject_ids','participant_id','participant_ids',
               'death_date','onset','date_of_birth','followup_years','observed'}
    for item in manifest['files']:
        if item['path'].endswith(('.csv','.csv.gz')):
            skip=1 if item['path'].endswith('subregion_func_network_Yeo_updated.csv') else 0
            header=set(pd.read_csv(ROOT/item['path'],nrows=0,skiprows=skip).columns.str.lower())
            assert not (header & forbidden), f"Restricted input fields: {item['path']}"

    for name in ['cox_per10_final.csv','cox_perSD_final.csv']:
        d=read('Cox/02_Results/'+name)
        select=d.feature.ne('125_400mg')
        q=multipletests(d.loc[select,'p_value'],alpha=.05,method='fdr_bh')[1]
        np.testing.assert_allclose(q,d.loc[select,'p_fdr_within_11'],rtol=1e-10,atol=1e-12)
        assert select.sum()==11
    d=read('Cox/02_Results/rcs_nonlinearity_results.csv')
    select=d.feature.ne('125_400mg')
    assert select.sum()==10 and '375_400mg' not in set(d.feature)
    q=multipletests(d.loc[select,'p_nonlinearity'],alpha=.05,method='fdr_bh')[1]
    np.testing.assert_allclose(q,d.loc[select,'p_nonlinearity_fdr'],rtol=1e-10,atol=1e-12)
    assert int((q<.05).sum())==7
    d=read('Cox/02_Results/PH_exposure_package.csv')
    select=d.feature.ne('125_400mg')
    q=multipletests(d.loc[select,'ph_p'],alpha=.05,method='fdr_bh')[1]
    np.testing.assert_allclose(q,d.loc[select,'ph_p_fdr_within_11'],rtol=1e-10,atol=1e-12)

    completed=subprocess.run([sys.executable,str(ROOT/'MLR/01_Code/verify_results.py'),
                              '--package',str(ROOT/'MLR')],check=True,capture_output=True,text=True)
    report={'files_checked':len(manifest['files']),'cox_fdr_checks_passed':True,
            'mlr_fdr':json.loads(completed.stdout)}
    spec=importlib.util.spec_from_file_location('release_annotation',ROOT/'MLR/01_Code/reused_annotation.py')
    annotation=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(annotation)
    annotation.INPUT=ROOT/'MLR/01_Code/atlas_reference'
    annotation.validate_mapping()
    index=read('MLR/02_Results/SC_retained_edge_index.csv').set_index('original_edge')
    for model,records,unique in [('Model1',86,79),('Model2',34,25)]:
        d=read(f'MLR/02_Results/{model}_all_significant_annotated.csv')
        assert len(d)==records and d.edge.nunique()==unique
        assert (d.effect_target>0).all() and (d.p_FDR_global_11bands<.05).all()
        np.testing.assert_array_equal(d.ROI_i,index.loc[d.edge,'ROI_i'])
        np.testing.assert_array_equal(d.ROI_j,index.loc[d.edge,'ROI_j'])
        observed=read(f'MLR/02_Results/{model}_network_matrix_unique.csv')
        observed=observed.set_index(observed.columns[0])
        expected=annotation.network_matrix(d,True)
        np.testing.assert_array_equal(observed.to_numpy(),expected.to_numpy())
        assert int(np.tril(observed.to_numpy()).sum())==unique
        if model=='Model2':
            assert (d.p_MDD_FDR_within_band<.05).all()
            assert (d.CI95_low_MDD>0).all() and (d.p_HC_FDR_within_band>=.05).all()
    report['atlas_edge_and_network_checks_passed']=True
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
