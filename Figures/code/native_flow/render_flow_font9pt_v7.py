"""Set all exclusion labels and the external matching annotation to 9 pt.
Main flow remains 10 pt; preserve wording, palette, and inward exclusion arrows.
Widen the three A exclusions, reserving extra page width on the right.
"""
import argparse
import render_flow_large_type_v5 as base


class NinePointPanel(base.LargePanel):
    def box(self,name,x,y,w,h,text,**kwargs):
        if name=='prevalent-exclusion': x,w=1,36
        if name=='case-qc-exclusion': x,w=1,34
        if name=='control-qc-exclusion': x,w=106,34
        super().box(name,x,y,w,h,text,**kwargs)

    def edge(self,points,arrow=True,meaning='sequence'):
        if points==[(30,84),(54.5,84)]: points=[(37,84),(54.5,84)]
        if points==[(30,122),(54.5,122)]: points=[(35,122),(54.5,122)]
        super().edge(points,arrow,meaning)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--full',action='store_true')
    base.EXCLUSION=base.MATCHING=9.0
    base.EXCLUSION_LEADING=base.MATCHING_LEADING=12.2
    base.AW=142
    base.TAG='font9pt_v7'
    base.OUT=base.base.HERE/'flow_font9pt_v7'
    base.OUT.mkdir(exist_ok=True)
    base.LargePanel=NinePointPanel
    base.main(parser.parse_args().full)
    print('Verified all exclusion labels and matching annotation at exactly 9 pt.')
