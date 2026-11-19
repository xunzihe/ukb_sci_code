%% Render the final Model 1 and Model 2 connectomes using BrainNet Viewer.
% No model estimation or changes to the BrainNet Viewer source code.
clear; clc; close all;
project_dir = fileparts(fileparts(mfilename('fullpath')));
for model_index = 1:2
    render_one(fullfile(project_dir, sprintf('Model%d', model_index)));
end

function render_one(root_dir)
input_dir = fullfile(root_dir, 'inputs');
output_dir = fullfile(root_dir, 'outputs', 'raw_views');
if ~exist(output_dir, 'dir'), mkdir(output_dir); end
settings = jsondecode(fileread(fullfile(input_dir, 'render_settings.json')));
addpath(genpath(settings.brainnet_root));
set(0, 'DefaultFigureVisible', 'off');
global EC surf
h0 = BrainNet_MapCfg(settings.surface_file);
EC_base = EC;
if ishghandle(h0), close(h0); end
EC = EC_base;
EC.bak.color = [1 1 1];
EC.msh.color = [.90 .90 .90];
EC.msh.alpha = settings.mesh_alpha;
EC.msh.boundary = 1;
EC.msh.doublebrain = 0;
EC.nod.draw = 1;
EC.nod.draw_threshold_type = 1;
EC.nod.draw_threshold = 0;
EC.nod.size = 2;
EC.nod.size_value = 2; % Respect the input radii instead of automatic rescaling.
EC.nod.size_ratio = settings.node_size_ratio;
EC.nod.color = 3;
EC.nod.CM = settings.network_rgb;
EC.nod.CMm = settings.network_rgb;
EC.nod.CMt = settings.network_rgb;
EC.lbl = 2; % No anatomical text labels over the dense graph.
EC.edg.draw = 1;
EC.edg.draw_threshold = 0;
EC.edg.draw_abs = 1;
EC.edg.size = 1;
EC.edg.size_size = settings.edge_radius;
EC.edg.size_ratio = 1;
EC.edg.size_abs = 1;
EC.edg.directed = 0;
EC.edg.interhemiedges = 0; % 1 means interhemispheric-only in this version; 0 retains ALL edges.
EC.edg.color = 2;
EC.edg.color_abs = 0;
EC.edg.color_map_type = 2;
EC.edg.color_map_low = settings.t_min;
EC.edg.color_map_high = settings.t_max;
EC.edg.opacity = 1;
EC.edg.opacity_same = settings.edge_opacity;
EC.edg.CM = settings.edge_colormap_rgb; % Shared standard sequential palette, 64 levels.
EC.edg.CMt = EC.edg.CM;
EC.glb.detail = 3;
EC.glb.render = 'OpenGL';
EC.glb.material = 'dull';
EC.glb.lighting = 'gouraud';
EC.glb.lr = 0;
EC.lot.view = 1;
EC.lot.view_direction = 4;
EC.img.width = 2000;
EC.img.height = 2000;
EC.img.dpi = 400;
EC_base = EC;
node_file = fullfile(input_dir, 'connectome.node');
edge_file = fullfile(input_dir, 'connectome.edge');
view_names = {'left', 'right', 'superior'};
angles = [-90 0; 90 0; 0 90];
render_check = struct;
for k = 1:3
    EC = EC_base;
    EC.lot.view_az = angles(k, 1);
    EC.lot.view_el = angles(k, 2);
    cfg_file = fullfile(input_dir, [settings.model '_' view_names{k} '_cfg.mat']);
    save(cfg_file, 'EC');
    fprintf('Rendering %s: %s view\n', settings.model, view_names{k});
    h = BrainNet_MapCfg(settings.surface_file, node_file, edge_file, cfg_file);
    set(h, 'Visible', 'off', 'Color', [1 1 1], 'Position', [100 100 1100 1100]);
    delete(findall(h, 'Type', 'colorbar'));
    extra_axes = findall(h, 'Type', 'axes', 'Tag', 'Colorbar');
    delete(extra_axes);
    axes_list = findall(h, 'Type', 'axes');
    counts = arrayfun(@(a) numel(findall(a, 'Type', 'patch')), axes_list);
    [~, which_axis] = max(counts);
    ax = axes_list(which_axis);
    set(ax, 'Position', [.025 .025 .95 .95], 'Visible', 'off');
    view(ax, angles(k, 1), angles(k, 2));
    axis(ax, 'equal');
    axis(ax, 'tight');
    axis(ax, 'vis3d');
    % BrainNet detail=3 creates 101x101 sphere meshes. Restore only node
    % lighting; retain unlit edge colors so t is not confused with shading.
    objects = findall(ax, 'Type', 'surface');
    node_count = 0; edge_count = 0;
    for object_index = 1:numel(objects)
        obj = objects(object_index);
        if isequal(size(get(obj, 'XData')), [101 101])
            set(obj, 'FaceLighting', 'gouraud', 'AmbientStrength', .38, ...
                'DiffuseStrength', .65, 'SpecularStrength', .20, 'SpecularExponent', 20);
            node_count = node_count + 1;
        else
            set(obj, 'FaceLighting', 'none');
            edge_count = edge_count + 1;
        end
    end
    assert(node_count == 246 && edge_count == settings.unique_edges, 'Node/edge lighting classification failed');
    drawnow;
    render_check.(view_names{k}).patches = numel(findall(ax, 'Type', 'patch'));
    render_check.(view_names{k}).mesh_objects = numel(findall(ax, 'Type', 'surface'));
    render_check.(view_names{k}).loaded_nodes = surf.nsph;
    render_check.(view_names{k}).loaded_unique_edges = nnz(triu(surf.net, 1));
    render_check.(view_names{k}).actual_rendered_edges = surf.ncyl;
    render_check.(view_names{k}).lit_3D_nodes = node_count;
    render_check.(view_names{k}).unlit_edges = edge_count;
    assert(surf.nsph == 246 && nnz(triu(surf.net, 1)) == settings.unique_edges);
    assert(surf.ncyl == settings.unique_edges, 'BrainNet filtered significant connections');
    assert(numel(findall(ax, 'Type', 'surface')) == 246 + settings.unique_edges, 'Actual node/edge object count differs');
    image_file = fullfile(output_dir, [settings.model '_' view_names{k} '.png']);
    exportgraphics(ax, image_file, 'Resolution', 400, 'BackgroundColor', 'white');
    fprintf('Saved %s\n', image_file);
    close(h);
end
fid = fopen(fullfile(root_dir, 'render_checks.json'), 'w');
fwrite(fid, jsonencode(render_check), 'char');
fclose(fid);
fprintf('%s rendering complete.\n', settings.model);
end
