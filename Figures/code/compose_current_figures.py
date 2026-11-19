"""Compose current Cox/RCS and anatomical/network figures from saved aggregates.

No models or statistical corrections are rerun. Anatomical panels are reused;
the network matrices count every significant unique ROI pair across all bands.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.patches import Rectangle
import pymupdf as fitz

plt.rcParams.update({'font.family':'Arial','font.size':7.5,'pdf.fonttype':42,
                     'svg.fonttype':'path','text.usetex':False,
                     'mathtext.fontset':'custom','mathtext.rm':'Arial',
                     'mathtext.it':'Arial:italic','mathtext.bf':'Arial:bold'})
MM=72/25.4
NETWORKS=['SC','VIS','SMN','DAN','VAN','LIM','FPN','DMN']
LABELS=['Subcortical',*NETWORKS[1:]]
BLUE='#1769AA'
SHADE='#A8CEE8'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def emit(fig,stem):
    fig.canvas.draw()
    renderer=fig.canvas.get_renderer()
    groups=[list(fig.texts)]
    for ax in fig.axes:
        xlim=sorted(ax.get_xlim()); ylim=sorted(ax.get_ylim())
        texts=[*ax.texts,ax.title]
        if ax.axison:
            texts += [ax.xaxis.label,ax.yaxis.label]
            texts += [t for t in ax.get_xticklabels() if xlim[0]<=t.get_position()[0]<=xlim[1]]
            texts += [t for t in ax.get_yticklabels() if ylim[0]<=t.get_position()[1]<=ylim[1]]
        groups.append([t for t in texts if t.get_visible() and t.get_text()])
    entries=[]
    for gi,group in enumerate(groups):
        for text in group:
            if not text.get_text(): continue
            box=text.get_window_extent(renderer)
            assert fig.bbox.contains(box.x0,box.y0) and fig.bbox.contains(box.x1,box.y1),(stem.name,'clipped',text.get_text())
            entries.append((gi,text.get_text(),box))
    for i,(gi,txt,box) in enumerate(entries):
        for gj,other,bb in entries[i+1:]:
            if gi!=gj:
                assert not box.overlaps(bb),(stem.name,'cross-panel text overlap',txt,other)
    fig.savefig(stem.with_suffix('.pdf'),facecolor='white')
    fig.savefig(stem.with_suffix('.svg'),facecolor='white')
    plt.close(fig)

def pval(p):
    if p<.001:
        mantissa,exponent=f'{p:.2e}'.split('e')
        return rf'{mantissa} $\times 10^{{{int(exponent)}}}$'
    return f'{p:.4f}'

def curve_crossings(x,y,target):
    """Read all intersections with the saved plotted polyline; no extrapolation."""
    x=np.asarray(x,dtype=float); y=np.asarray(y,dtype=float)
    assert np.all(np.diff(x)>0)
    crossings=x[np.isclose(y,target,rtol=0,atol=1e-12)].tolist()
    for i in np.flatnonzero((y[:-1]-target)*(y[1:]-target)<0):
        order=np.argsort(y[i:i+2])
        crossings.append(float(np.interp(target,y[i:i+2][order],x[i:i+2][order])))
    return np.unique(crossings).tolist()

def draw_curve(fig,rect,feature,stats,root,letter,target_hr=None,ticks_inward=False):
    row=stats.loc[feature]
    curve=pd.read_csv(root/'data/cox/curves'/f'rcs_curve_{feature}.csv')
    assert len(curve)==350 and curve.feature.eq(feature).all()
    x=curve.minutes_per_week.to_numpy(float)
    y=curve.HR.to_numpy(float)
    lo=curve.CI95_low.to_numpy(float); hi=curve.CI95_high.to_numpy(float)
    assert (lo<=y).all() and (y<=hi).all()
    assert np.isclose(x[0],row.reference_min_week) and np.isclose(y[0],1)
    ax=fig.add_axes(rect)
    ax.fill_between(x,lo,hi,color=SHADE,alpha=.48,lw=0)
    line,=ax.plot(x,y,color=BLUE,lw=1.3)
    np.testing.assert_array_equal(line.get_ydata(),y)
    ax.axhline(1,color='#555555',lw=.6,linestyle=(0,(3,2)))
    ax.set_xlim(x.min(),x.max()); ax.set_ylim(.2,1.08)
    ax.set_yticks([.2,.4,.6,.8,1.0])
    ax.xaxis.set_major_locator(MaxNLocator(nbins=3,min_n_ticks=3))
    ax.tick_params(labelsize=6.4,pad=1.5,length=2)
    if ticks_inward:
        # Keep labels at their original positions while ticks point into the plot.
        ax.tick_params(axis='both',which='both',direction='in',pad=3.5)
    ax.set_xlabel('Duration (min/week)',fontsize=6.8,labelpad=2)
    ax.set_ylabel('Adjusted HR',fontsize=6.8,labelpad=2)
    for side in ['top','right']: ax.spines[side].set_visible(False)
    for side in ['left','bottom']: ax.spines[side].set_linewidth(.6)
    ax.grid(axis='y',color='#E7E7E7',lw=.4); ax.set_axisbelow(True)
    guide=None
    if target_hr is not None:
        color='#C62828'
        crossings=curve_crossings(x,y,target_hr)
        ax.set_yticks(sorted(set([*ax.get_yticks(),target_hr])))
        ax.axhline(target_hr,color=color,lw=.75,linestyle=(0,(3,2.4)),zorder=3)
        for value in crossings:
            ax.vlines(value,.2,target_hr,color=color,lw=.65,linestyle=(0,(3,2.4)),zorder=3)
            ax.plot(value,target_hr,'o',ms=3,mfc=color,mec=color,mew=.75,zorder=5)
            alignment='right' if (value-x.min())/(x.max()-x.min())>.85 else 'left'
            offset=-3 if alignment=='right' else 3
            ax.annotate(f'{value:.1f}',xy=(value,target_hr+.08),xytext=(offset,0),
                        textcoords='offset points',ha=alignment,va='center',fontsize=6,
                        color=color,zorder=6)
        if not crossings:
            ax.text(.97,.315,'Not reached',transform=ax.get_yaxis_transform(),
                    ha='right',va='center',fontsize=5.8,color=color,zorder=6)
        for label in ax.get_yticklabels():
            if np.isclose(float(label.get_text()),target_hr):
                label.set_color(color); label.set_fontweight('bold')
        guide={'HR':float(target_hr),'reference_min_week':float(row.reference_min_week),
               'duration_min_week':crossings,
               'additional_duration_from_reference':[v-float(row.reference_min_week) for v in crossings],
               'interpolation':'numpy.interp along the saved plotted polyline; no extrapolation',
               'interpretation':'Model point estimates relative to the band-specific reference, not a treatment threshold.'}
    ax.text(.025,.06,f'Ref: {row.reference_min_week:g} min/week',transform=ax.transAxes,
            fontsize=6,va='bottom',color='#33475b',zorder=7,
            bbox=dict(facecolor='white',edgecolor='none',pad=.4) if target_hr is not None else None)
    ax.text(-.16,1.36,letter,transform=ax.transAxes,fontsize=10,fontweight='bold',va='bottom')
    ax.text(.5,1.38,feature.replace('_','-').replace('mg',' mg'),transform=ax.transAxes,
            ha='center',va='bottom',fontweight='bold',fontsize=8)
    ax.text(.5,1.19,f'Nonlinearity P = {pval(row.p_nonlinearity)}',transform=ax.transAxes,
            ha='center',va='bottom',fontsize=6)
    ax.text(.5,1.05,f'FDR P = {pval(row.p_nonlinearity_fdr)}',transform=ax.transAxes,
            ha='center',va='bottom',fontsize=6)
    return {'feature':feature,'points':len(curve),'p_nonlinearity':float(row.p_nonlinearity),
            'p_FDR':float(row.p_nonlinearity_fdr),'curve_sha256':sha(root/'data/cox/curves'/f'rcs_curve_{feature}.csv'),
            'HR_guide':guide}

def combined_cox(root,out,stats):
    width,height=166,221
    fig=plt.figure(figsize=(width/25.4,height/25.4),facecolor='white')
    bands=[f'{a}_{a+25}mg' for a in range(125,400,25)]
    df=pd.read_csv(root/'data/cox/cox_per10_final.csv').set_index('feature')
    df=df.loc[bands[::-1]+['125_400mg']]
    assert df.n.eq(94536).all() and df.events.eq(735).all()
    ax=fig.add_axes([.265,.718,.43,.227])
    ax.set_xlim(.65,1.015); ax.set_ylim(11.7,-.7)
    ax.set_yticks([]); ax.set_xticks([.7,.8,.9,1.0]); ax.tick_params(labelsize=7,length=2)
    ax.tick_params(axis='x',which='both',direction='in',pad=5.5)
    ax.axvline(1,color='#666666',lw=.7,linestyle=(0,(3,3)))
    ax.grid(axis='x',color='#e4e8ec',lw=.5); ax.set_axisbelow(True)
    for side in ['left','top','right']: ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_linewidth(.6)
    ax.set_xlabel('Adjusted hazard ratio per 10 min/week',fontsize=7.3,labelpad=3)
    pal=dict(zip(bands,plt.cm.Blues(np.linspace(.48,.90,11))))
    pal['125_400mg']='#E9B526'
    fig.text(.018,.981,'A',fontsize=11,fontweight='bold',va='top')
    fig.text(.045,.962,'Intensity band',fontsize=7.8,fontweight='bold',va='center')
    fig.text(.845,.962,'Adjusted HR (95% CI)',fontsize=7.4,fontweight='bold',ha='center',va='center')
    vals=[]
    for i,(feature,row) in enumerate(df.iterrows()):
        hr=float(row.HR_per_10min); lower=float(row.CI95_low_per_10min); upper=float(row.CI95_high_per_10min)
        assert lower<hr<upper
        ax.hlines(i,lower,upper,color=pal[feature],lw=1.4)
        ax.scatter(hr,i,color=pal[feature],s=22,edgecolor='white',linewidth=.5,zorder=3)
        yy=.718+.227*(1-(i+.7)/12.4)
        label='MPA 125-400 mg' if feature=='125_400mg' else feature.replace('_','-').replace('mg',' mg')
        weight='bold' if feature=='125_400mg' else 'normal'
        fig.text(.045,yy,label,fontsize=7.4,fontweight=weight,va='center')
        fig.text(.845,yy,f'{hr:.3f} ({lower:.3f}-{upper:.3f})',fontsize=7.4,
                 fontweight=weight,ha='center',va='center')
        vals.append({'feature':feature,'HR':hr,'CI_low':lower,'CI_high':upper})
    curves=[]
    positions=[(.105,.495),(.425,.495),(.745,.495),
               (.105,.270),(.425,.270),(.745,.270),(.425,.045)]
    for i,(feature,(left,bottom)) in enumerate(zip(bands[:7],positions)):
        assert stats.loc[feature,'p_nonlinearity_fdr']<.05
        curves.append(draw_curve(fig,[left,bottom,.235,.112],feature,stats,root,chr(66+i),target_hr=.6,ticks_inward=True))
    emit(fig,out/'Figure_2_combined')
    return {'forest_rows':vals,'nonlinear_panels':curves,'n':94536,'events':735}

def other_rcs(root,out,stats):
    fig=plt.figure(figsize=(166/25.4,111/25.4),facecolor='white')
    result=[]
    for i,feature in enumerate(['300_325mg','325_350mg','350_375mg']):
        left,bottom=[(.11,.57),(.6,.57),(.355,.1)][i]
        assert stats.loc[feature,'p_nonlinearity_fdr']>=.05
        result.append(draw_curve(fig,[left,bottom,.33,.255],feature,stats,root,chr(65+i)))
    emit(fig,out/'Supplementary_Figure_S2_RCS')
    return result

def matrices(root,out):
    collection={}; counts={}
    for name,term,nrec,nuniq in [('Model1','PA',86,79),('Model2','Int',34,25)]:
        df=pd.read_csv(root/f'data/mlr/{name}_all_significant_annotated.csv')
        assert len(df)==nrec and df.edge_key.nunique()==nuniq
        assert (df.p_FDR_global_11bands<.05).all() and (df[f't_{term}']>0).all()
        assert df.groupby('edge_key')[['ROI_i','ROI_j','net_i','net_j']].nunique().max().max()==1
        unique=df.sort_values(f't_{term}',ascending=False).drop_duplicates('edge_key')
        matrix=np.zeros((8,8),dtype=int)
        for row in unique.itertuples():
            i,j=sorted([NETWORKS.index(row.net_i),NETWORKS.index(row.net_j)],reverse=True)
            matrix[i,j]+=1
        assert matrix.sum()==nuniq
        pd.DataFrame(matrix,index=LABELS,columns=LABELS).to_csv(out/f'{name}_network_unique_edges_lower_triangle.csv')
        collection[name]=matrix
        counts[name]={'records':nrec,'unique_edges':nuniq,'matrix_lower_triangle_sum':int(matrix.sum()),
                      'unique_network_pair_counts':unique.network_pair.value_counts().to_dict(),
                      'record_network_pair_counts':df.network_pair.value_counts().to_dict(),
                      'unique_connection_classes':unique.connection_class.value_counts().to_dict()}
    fig,axes=plt.subplots(1,2,figsize=(166/25.4,79/25.4))
    fig.subplots_adjust(left=.105,right=.895,bottom=.26,top=.90,wspace=.55)
    vmax=max(m.max() for m in collection.values())
    cmap=plt.colormaps['Blues'].copy(); cmap.set_bad('white')
    norm=matplotlib.colors.Normalize(vmin=0,vmax=vmax)
    image=matplotlib.cm.ScalarMappable(norm=norm,cmap=cmap)
    for k,(ax,(name,m)) in enumerate(zip(axes,collection.items())):
        # A cell's fill and border share exactly the same vector path. Avoid
        # independently sampled imshow pixels beneath separate grid rectangles.
        ax.set_xlim(-.5,7.5);ax.set_ylim(7.5,-.5)
        ax.set_aspect('equal',adjustable='box')
        for i in range(8):
            for j in range(i+1):
                ax.add_patch(Rectangle((j-.5,i-.5),1,1,
                    facecolor=cmap(norm(m[i,j])),edgecolor='#292929',lw=.45,
                    antialiased=False,snap=False,joinstyle='miter',clip_on=False))
                ax.text(j,i,str(m[i,j]),ha='center',va='center',fontsize=7,
                        color='white' if m[i,j]>vmax*.6 else '#1b1b1b')
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.set_xticks(range(8),LABELS,rotation=55,ha='right',fontsize=6)
        ax.set_yticks(range(8),LABELS,fontsize=6)
        # Retain label spacing, but do not draw ticks outside the matrix cells.
        ax.tick_params(axis='both',which='both',length=2,pad=2,
                       bottom=False,top=False,left=False,right=False)
        ax.set_title(f'{name.replace("Model","Model ")}',fontsize=9,pad=8)
        ax.text(-.27,1.12,chr(67+k),transform=ax.transAxes,fontsize=11,fontweight='bold',va='top')
    cax=fig.add_axes([.927,.285,.018,.53])
    cb=fig.colorbar(image,cax=cax,ticks=range(0,vmax+1,2))
    cb.ax.tick_params(labelsize=6.5,length=2)
    cb.set_label('Unique SC edges',fontsize=7,labelpad=4)
    emit(fig,out/'Network_matrices_CD')
    return counts

def brain_four_panels(root,out,panels=None):
    palette=pd.read_csv(root/'brain/Model1/inputs/Network_color_key.csv').set_index('Network')
    legend_figure=plt.figure(figsize=(166/25.4,20/25.4),facecolor='white')
    legend_ax=legend_figure.add_axes([0,0,1,1]); legend_ax.axis('off')
    for i,network in enumerate(['DMN','VIS','VAN','SMN','LIM','FPN','DAN','SC']):
        x=.07 if i<4 else .53; y=.88-(i%4)*.23
        row=palette.loc[network]; color=row[['R','G','B']].to_numpy(float)
        legend_ax.add_patch(Rectangle((x,y-.055),.018,.11,facecolor=color,edgecolor='none'))
        label=row['Name']+(f' ({network})' if network!='SC' else '')
        legend_ax.text(x+.029,y,label,fontsize=6.5,ha='left',va='center')
    emit(legend_figure,out/'Shared_network_legend')
    # Preserve both approved anatomical panels, including their A/B letters.
    panels=panels or {name:root/f'brain/approved_panels/{name}_brain_connectome_3D.pdf' for name in ['Model1','Model2']}
    with fitz.open(panels['Model1']) as a, \
         fitz.open(panels['Model2']) as b, \
         fitz.open(out/'Network_matrices_CD.pdf') as mat, \
         fitz.open(out/'Shared_network_legend.pdf') as legend, fitz.open() as doc:
        # Reposition existing PDF fragments at unit scale. Brain rasters, text,
        # matrix paths and all statistical values retain their physical sizes.
        width=166*MM; hbrain=60*MM; gap=1.5*MM; hlegend=9.5*MM
        legend_top=2*hbrain+gap+1*MM
        matrix_top=legend_top+hlegend+gap
        matrix_clip=fitz.Rect(0,.7*MM,width,71.2*MM)
        page=doc.new_page(width=width,height=matrix_top+matrix_clip.height)
        placements=[]

        def place(source, source_box_mm, left_mm, top_mm, label):
            clip=fitz.Rect(*(value*MM for value in source_box_mm)) & source[0].rect
            destination=fitz.Rect(left_mm*MM,top_mm*MM,
                                  left_mm*MM+clip.width,top_mm*MM+clip.height)
            assert (page.rect+(-.001,-.001,.001,.001)).contains(destination), (label,destination,page.rect)
            page.show_pdf_page(destination,source,0,clip=clip,keep_proportion=False)
            placements.append({'part':label,'source_mm':list(source_box_mm),
                               'destination_mm':[value/MM for value in destination],
                               'scale_x':destination.width/clip.width,
                               'scale_y':destination.height/clip.height})

        for source,label,top in [(a,'A',0),(b,'B',(hbrain+gap)/MM)]:
            # The side views move upward by 5 mm; the superior view stays put.
            place(source,[0,7,112,52],0,top+2,label+'_lateral_views')
            place(source,[112,0,166,60],112,top,label+'_superior_view_and_heading')
            # Put the complete original colourbar in the unused lateral-view area.
            place(source,[35,60,131,72.5],8,top+46,label+'_colourbar')
            place(source,[0,0,112,7],0,top,label+'_letter_and_lateral_headings')

        # Move the eight unchanged legend entries into four columns and two rows.
        spans=[span for block in legend[0].get_text('dict')['blocks'] if 'lines' in block
               for line in block['lines'] for span in line['spans']]
        entries=[]
        for index,network in enumerate(['DMN','VIS','VAN','SMN','LIM','FPN','DAN','SC']):
            row=palette.loc[network]
            label=row['Name']+(f' ({network})' if network!='SC' else '')
            span=next(span for span in spans if span['text']==label)
            text_box=fitz.Rect(span['bbox'])
            swatch_left=(.07 if index<4 else .53)*166
            center_y=(1-(.88-(index%4)*.23))*20
            swatch=fitz.Rect(swatch_left*MM,(center_y-1.1)*MM,
                             (swatch_left+2.988)*MM,(center_y+1.1)*MM)
            clip=text_box|swatch
            clip+=(-.25*MM,-.25*MM,.25*MM,.25*MM)
            entries.append((label,clip))
        column_widths=[max(entries[column][1].width,entries[column+4][1].width)/MM
                       for column in range(4)]
        used_width=sum(column_widths)+3*3
        assert used_width<164
        left=(166-used_width)/2
        for column in range(4):
            for row_index in range(2):
                label,clip=entries[column+4*row_index]
                place(legend,[value/MM for value in clip],left,
                      legend_top/MM+1+4.2*row_index,'legend_'+label)
            left+=column_widths[column]+3

        place(mat,[value/MM for value in matrix_clip],0,matrix_top/MM,'matrices_C_D')
        assert all(abs(item['scale_x']-1)<1e-12 and abs(item['scale_y']-1)<1e-12
                   for item in placements)
        doc.save(out/'Figure_3_connectomes_and_matrices.pdf',garbage=4,deflate=True)
        (out/'Figure_3_layout.json').write_text(json.dumps({
            'width_mm':166,'height_mm':page.rect.height/MM,
            'original_height_mm':257,'content_scaling':1,
            'brain_lateral_translation_mm':[0,-5],
            'colourbar_translation_mm':[-27,-14],
            'legend_arrangement':'four columns, two rows',
            'placements':placements,'statistics_changed':False,
            'fonts_and_line_widths_changed':False,
        },indent=2),encoding='utf-8')

