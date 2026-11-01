from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.io import loadmat
ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data' / 'input'
NETWORK_ORDER = ['SC', 'VIS', 'SMN', 'DAN', 'VAN', 'LIM', 'FPN', 'DMN']

def validate_mapping() -> tuple[pd.DataFrame, pd.DataFrame]:
    mapping = pd.read_csv(INPUT / 'brainnetome_official_yeo7_yeo17_mapping.csv')
    official = pd.read_csv(INPUT / 'subregion_func_network_Yeo_updated.csv', skiprows=1, usecols=range(5))
    check = mapping.merge(official, left_on='BN_Index', right_on='Label', validate='one_to_one')
    assert len(check) == 246
    assert official['Label'].tolist() == list(range(1, 247))
    assert (check['Region_official'].astype(str) == check['region'].astype(str)).all()
    assert (check['Yeo7_Network'].astype(int) == check['Yeo_7network'].astype(int)).all()
    assert (check['Yeo17_Network'].astype(int) == check['Yeo_17network'].astype(int)).all()
    hierarchy = pd.read_csv(INPUT / 'Brainnetome_subcortical_36node_hierarchy.csv')
    assert set(hierarchy['BN_Index']) == set(range(211, 247))
    return (mapping, hierarchy)

def annotate(path: Path, model: str, mapping: pd.DataFrame, hierarchy: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(path)
    df['Dataset'] = model
    df['edge_key'] = df.apply(lambda r: f'{min(int(r.ROI_i), int(r.ROI_j)):03d}-{max(int(r.ROI_i), int(r.ROI_j)):03d}', axis=1)
    map_cols = ['BN_Index', 'Region_official', 'Hemisphere', 'Cyto_Label', 'Gyrus', 'Lobe', 'Yeo7_Name', 'Yeo7_Abbreviation', 'Is_Cortical']
    for side in ('i', 'j'):
        rename = {x: f'{x}_{side}' for x in map_cols if x != 'BN_Index'}
        rename['BN_Index'] = f'ROI_{side}'
        df = df.merge(mapping[map_cols].rename(columns=rename), on=f'ROI_{side}', how='left', validate='many_to_one')
    hcols = ['BN_Index', 'Structure', 'Bilateral_subregion', 'Raw_node']
    for side in ('i', 'j'):
        rename = {x: f'{x}_{side}' for x in hcols if x != 'BN_Index'}
        rename['BN_Index'] = f'ROI_{side}'
        df = df.merge(hierarchy[hcols].rename(columns=rename), on=f'ROI_{side}', how='left', validate='many_to_one')
    assert df[['Region_official_i', 'Region_official_j']].notna().all().all()
    df['net_i'] = df['Yeo7_Abbreviation_i'].fillna('SC')
    df['net_j'] = df['Yeo7_Abbreviation_j'].fillna('SC')
    df['network_pair'] = df.apply(lambda r: '-'.join(sorted([r.net_i, r.net_j], key=NETWORK_ORDER.index)), axis=1)
    df['connection_class'] = np.select([(df['net_i'] != 'SC') & (df['net_j'] != 'SC'), (df['net_i'] == 'SC') & (df['net_j'] == 'SC')], ['Cortical-Cortical', 'Subcortical-Subcortical'], default='Subcortical-Cortical')
    tcol = 't_PA' if model == 'Model1' else 't_Int'
    effect = 'beta_PA' if model == 'Model1' else 'beta_Int'
    df['effect_target'] = pd.to_numeric(df[effect], errors='raise')
    df['abs_t'] = pd.to_numeric(df[tcol], errors='raise').abs()
    return df

def network_matrix(df: pd.DataFrame, unique: bool) -> pd.DataFrame:
    use = df.sort_values('abs_t', ascending=False)
    if unique:
        use = use.drop_duplicates('edge_key')
    matrix = pd.DataFrame(0, index=NETWORK_ORDER, columns=NETWORK_ORDER, dtype=int)
    for r in use.itertuples():
        matrix.loc[r.net_i, r.net_j] += 1
        if r.net_i != r.net_j:
            matrix.loc[r.net_j, r.net_i] += 1
    return matrix
