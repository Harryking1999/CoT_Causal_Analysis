import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoModel
from collections import defaultdict

class SimplifiedParameterAnalyzer:
    def __init__(self, path_base, path_new_list):
        self.path_base = path_base
        self.path_new_list = path_new_list if isinstance(path_new_list, list) else [path_new_list]
        self.base_model = None
        self.new_models = []
        self.all_results = []  # 存储所有模型的结果
        self.global_scales = {}  # 存储全局尺度信息
        
    def load_models(self):
        """加载基线模型和所有新模型"""
        print("Loading base model...")
        try:
            self.base_model = AutoModel.from_pretrained(
                self.path_base, torch_dtype=torch.float32, trust_remote_code=True
            )
        except Exception as e:
            print(f"Error loading base model: {e}")
            return False
        
        print(f"Loading {len(self.path_new_list)} new models...")
        self.new_models = []
        for i, path_new in enumerate(self.path_new_list):
            try:
                model = AutoModel.from_pretrained(
                    path_new, torch_dtype=torch.float32, trust_remote_code=True
                )
                self.new_models.append(model)
                print(f"Loaded model {i+1}: {path_new}")
            except Exception as e:
                print(f"Error loading model {i+1} ({path_new}): {e}")
                return False
        
        return True
    
    def categorize_parameter(self, param_name):
        """参数分类 - 提取层号和组件类型"""
        layer_num = -1  # -1表示不属于特定层（如embedding, lm_head等）
        component = 'other'
        
        # 提取层号
        for pattern in ['layers.', 'layer.']:
            if pattern in param_name:
                try:
                    layer_num = int(param_name.split(pattern)[1].split('.')[0])
                    break
                except:
                    pass
        
        # 判断组件类型
        if any(x in param_name for x in ['self_attn', 'attention']):
            component = 'attention'
        elif any(x in param_name for x in ['mlp', 'feed_forward', 'ffn']):
            component = 'ffn'
        elif 'embed' in param_name:
            component = 'embedding'
        elif any(x in param_name for x in ['norm', 'layer_norm']):
            component = 'norm'
        elif 'lm_head' in param_name:
            component = 'lm_head'
            
        return layer_num, component
    
    def calculate_relative_l2_diff(self, model_index):
        """计算指定模型与基线的相对L2差异"""
        base_params = dict(self.base_model.named_parameters())
        new_params = dict(self.new_models[model_index].named_parameters())
        
        common_keys = set(base_params.keys()) & set(new_params.keys())
        print(f"Analyzing {len(common_keys)} common parameters for model {model_index+1}...")
        
        results = []
        
        for key in common_keys:
            base_param = base_params[key]
            new_param = new_params[key]
            
            if base_param.shape != new_param.shape:
                continue
                
            with torch.no_grad():
                # 计算相对L2差异作为主要指标
                diff = new_param - base_param
                diff_l2 = torch.norm(diff, p=2).item()
                base_l2 = torch.norm(base_param, p=2).item()
                relative_l2 = diff_l2 / (base_l2 + 1e-8)
                
                layer_num, component = self.categorize_parameter(key)
                param_count = base_param.numel()
                
                results.append({
                    'param_name': key,
                    'layer_num': layer_num,
                    'component': component,
                    'param_count': param_count,
                    'relative_l2_diff': relative_l2,
                    'model_index': model_index
                })
        
        return pd.DataFrame(results)
    
    def analyze_layer_differences(self, df):
        """分析每一层的参数差异"""
        print(f"\n{'='*60}")
        print(f"每一层参数差异分析 (Model {df['model_index'].iloc[0]+1})")
        print(f"{'='*60}")
        
        # 过滤出有层号的参数
        layer_df = df[df['layer_num'] >= 0].copy()
        
        if len(layer_df) == 0:
            print("未找到层级信息")
            return None
        
        # 计算每层的加权平均差异（按参数数量加权）
        layer_stats = []
        for layer_num in sorted(layer_df['layer_num'].unique()):
            layer_data = layer_df[layer_df['layer_num'] == layer_num]
            
            # 加权平均相对L2差异
            weighted_diff = np.average(
                layer_data['relative_l2_diff'], 
                weights=layer_data['param_count']
            )
            
            total_params = layer_data['param_count'].sum()
            
            layer_stats.append({
                'layer': layer_num,
                'weighted_avg_diff': weighted_diff,
                'total_params': total_params,
                'max_diff': layer_data['relative_l2_diff'].max()
            })
        
        layer_results = pd.DataFrame(layer_stats)
        print("各层参数差异统计:")
        print(layer_results.round(6))
        
        return layer_results
    
    def analyze_component_differences(self, df):
        """分析各组件的整体差异"""
        print(f"\n{'='*60}")
        print(f"各组件整体差异分析 (Model {df['model_index'].iloc[0]+1})")
        print(f"{'='*60}")
        
        component_stats = []
        for component in df['component'].unique():
            comp_data = df[df['component'] == component]
            
            # 加权平均相对L2差异
            weighted_diff = np.average(
                comp_data['relative_l2_diff'],
                weights=comp_data['param_count']
            )
            
            total_params = comp_data['param_count'].sum()
            
            component_stats.append({
                'component': component,
                'weighted_avg_diff': weighted_diff,
                'total_params': total_params,
                'max_diff': comp_data['relative_l2_diff'].max(),
                'param_percentage': total_params / df['param_count'].sum() * 100
            })
        
        comp_results = pd.DataFrame(component_stats).sort_values('weighted_avg_diff', ascending=False)
        print("各组件差异统计:")
        print(comp_results.round(6))
        
        return comp_results
    
    def analyze_layer_component_differences(self, df):
        """分析每一层的attention和ffn差异"""
        print(f"\n{'='*60}")
        print(f"每一层attention和ffn差异分析 (Model {df['model_index'].iloc[0]+1})")
        print(f"{'='*60}")
        
        # 只分析有层号的attention和ffn
        layer_df = df[df['layer_num'] >= 0]
        target_components = ['attention', 'ffn']
        layer_df = layer_df[layer_df['component'].isin(target_components)]
        
        if len(layer_df) == 0:
            print("未找到层级attention/ffn信息")
            return None, None
        
        layer_comp_stats = []
        for layer_num in sorted(layer_df['layer_num'].unique()):
            layer_data = layer_df[layer_df['layer_num'] == layer_num]
            
            for component in target_components:
                comp_data = layer_data[layer_data['component'] == component]
                
                if len(comp_data) > 0:
                    weighted_diff = np.average(
                        comp_data['relative_l2_diff'],
                        weights=comp_data['param_count']
                    )
                    total_params = comp_data['param_count'].sum()
                else:
                    weighted_diff = 0
                    total_params = 0
                
                layer_comp_stats.append({
                    'layer': layer_num,
                    'component': component,
                    'weighted_avg_diff': weighted_diff,
                    'total_params': total_params
                })
        
        layer_comp_results = pd.DataFrame(layer_comp_stats)
        
        # 透视表展示
        pivot_table = layer_comp_results.pivot(
            index='layer', 
            columns='component', 
            values='weighted_avg_diff'
        ).fillna(0)
        
        print("各层attention和ffn差异对比:")
        print(pivot_table.round(6))
        
        # 计算attention vs ffn的整体对比
        att_data = layer_comp_results[layer_comp_results['component'] == 'attention']
        ffn_data = layer_comp_results[layer_comp_results['component'] == 'ffn']
        att_total = att_data['weighted_avg_diff'].mean() if len(att_data) > 0 else 0
        ffn_total = ffn_data['weighted_avg_diff'].mean() if len(ffn_data) > 0 else 0
        
        print(f"\n整体对比:")
        print(f"Attention平均差异: {att_total:.6f}")
        print(f"FFN平均差异: {ffn_total:.6f}")
        print(f"FFN/Attention差异比例: {ffn_total/att_total:.3f}" if att_total > 0 else "")
        
        return layer_comp_results, pivot_table
    
    def calculate_global_scales(self):
        """计算所有模型的全局尺度，确保图表一致性"""
        print("Calculating global scales...")
        
        # 收集所有数据的统计信息
        all_layer_diffs = []
        all_comp_diffs = []
        all_hist_data = []
        all_att_ffn_diffs = []
        
        for df in self.all_results:
            # 层级差异
            layer_df = df[df['layer_num'] >= 0]
            if len(layer_df) > 0:
                layer_stats = layer_df.groupby('layer_num').apply(
                    lambda x: np.average(x['relative_l2_diff'], weights=x['param_count'])
                )
                all_layer_diffs.extend(layer_stats.values)
            
            # 组件差异
            comp_stats = df.groupby('component').apply(
                lambda x: np.average(x['relative_l2_diff'], weights=x['param_count'])
            )
            all_comp_diffs.extend(comp_stats.values)
            
            # 直方图数据
            all_hist_data.extend(df['relative_l2_diff'].values)
            
            # attention和ffn差异
            layer_df = df[df['layer_num'] >= 0]
            for comp in ['attention', 'ffn']:
                comp_data = layer_df[layer_df['component'] == comp]
                if len(comp_data) > 0:
                    comp_stats = comp_data.groupby('layer_num').apply(
                        lambda x: np.average(x['relative_l2_diff'], weights=x['param_count'])
                    )
                    all_att_ffn_diffs.extend(comp_stats.values)
        
        # 设置全局尺度
        self.global_scales = {
            'layer_y_max': max(all_layer_diffs) * 1.1 if all_layer_diffs else 1,
            'comp_y_max': max(all_comp_diffs) * 1.1 if all_comp_diffs else 1,
            'hist_y_max': None,  # 直方图用自动尺度
            'att_ffn_y_max': max(all_att_ffn_diffs) * 1.1 if all_att_ffn_diffs else 1,
            'hist_x_max': max(all_hist_data) if all_hist_data else 1
        }
    
    def create_visualizations(self, df, layer_results, comp_results, layer_comp_results, model_index):
        """创建统一尺度的可视化图表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 各层差异
        if layer_results is not None:
            axes[0, 0].bar(layer_results['layer'], layer_results['weighted_avg_diff'])
            axes[0, 0].set_title(f'Parameter Differences by Layer (Model {model_index+1})')
            axes[0, 0].set_xlabel('Layer Number')
            axes[0, 0].set_ylabel('Weighted Avg Relative L2 Diff')
            axes[0, 0].set_ylim(0, self.global_scales['layer_y_max'])
        
        # 2. 各组件差异
        axes[0, 1].bar(comp_results['component'], comp_results['weighted_avg_diff'])
        axes[0, 1].set_title(f'Parameter Differences by Component (Model {model_index+1})')
        axes[0, 1].set_xlabel('Component')
        axes[0, 1].set_ylabel('Weighted Avg Relative L2 Diff')
        axes[0, 1].tick_params(axis='x', rotation=45)
        axes[0, 1].set_ylim(0, self.global_scales['comp_y_max'])
        
        # 3. 各层attention vs ffn
        if layer_comp_results is not None:
            att_data = layer_comp_results[layer_comp_results['component'] == 'attention']
            ffn_data = layer_comp_results[layer_comp_results['component'] == 'ffn']
            
            if len(att_data) > 0 and len(ffn_data) > 0:
                x = att_data['layer']
                width = 0.35
                
                axes[1, 0].bar(x - width/2, att_data['weighted_avg_diff'], width, label='Attention')
                axes[1, 0].bar(x + width/2, ffn_data['weighted_avg_diff'], width, label='FFN')
                axes[1, 0].set_title(f'Attention vs FFN by Layer (Model {model_index+1})')
                axes[1, 0].set_xlabel('Layer Number')
                axes[1, 0].set_ylabel('Weighted Avg Relative L2 Diff')
                axes[1, 0].legend()
                axes[1, 0].set_ylim(0, self.global_scales['att_ffn_y_max'])
        
        # 4. 参数变化分布
        axes[1, 1].hist(df['relative_l2_diff'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[1, 1].set_title(f'Distribution of Relative L2 Differences (Model {model_index+1})')
        axes[1, 1].set_xlabel('Relative L2 Difference')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_xlim(0, self.global_scales['hist_x_max'])
        
        plt.tight_layout()
        plt.savefig(f'simplified_parameter_analysis_{model_index}.png', dpi=300, bbox_inches='tight')
        print(f"可视化图表已保存为 'simplified_parameter_analysis_{model_index}.png'")
    
    def categorize_layers_by_depth(self, layer_results_list):
        """将层分为低层、中层、高层"""
        if not layer_results_list or len(layer_results_list) == 0:
            return None
            
        # 假设所有模型都有相同的层数
        max_layer = max([lr['layer'].max() for lr in layer_results_list if lr is not None])
        
        # 分层策略：三等分
        low_layers = list(range(0, max_layer // 3))
        mid_layers = list(range(max_layer // 3, 2 * max_layer // 3))
        high_layers = list(range(2 * max_layer // 3, max_layer + 1))
        
        return low_layers, mid_layers, high_layers
    
    def create_trend_visualizations(self):
        """创建统一尺度的时序趋势可视化图表"""
        if len(self.all_results) < 2:
            print("需要至少2个模型才能绘制趋势图")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        # 收集所有模型的统计数据
        model_indices = list(range(len(self.all_results)))
        overall_diffs = []
        layer_group_diffs = {'low': [], 'mid': [], 'high': []}
        att_ffn_diffs = {'attention_low': [], 'attention_mid': [], 'attention_high': [],
                         'ffn_low': [], 'ffn_mid': [], 'ffn_high': []}
        
        # 获取层级分组
        layer_results_list = []
        for df in self.all_results:
            layer_df = df[df['layer_num'] >= 0]
            if len(layer_df) > 0:
                layer_stats = []
                for layer_num in sorted(layer_df['layer_num'].unique()):
                    layer_data = layer_df[layer_df['layer_num'] == layer_num]
                    weighted_diff = np.average(layer_data['relative_l2_diff'], weights=layer_data['param_count'])
                    layer_stats.append({'layer': layer_num, 'weighted_avg_diff': weighted_diff})
                layer_results_list.append(pd.DataFrame(layer_stats))
            else:
                layer_results_list.append(None)
        
        layer_groups = self.categorize_layers_by_depth(layer_results_list)
        
        for i, df in enumerate(self.all_results):
            # 1. 总体参数变化
            overall_diff = np.average(df['relative_l2_diff'], weights=df['param_count'])
            overall_diffs.append(overall_diff)
            
            # 2. 层级分组变化
            if layer_groups and layer_results_list[i] is not None:
                low_layers, mid_layers, high_layers = layer_groups
                layer_result = layer_results_list[i]
                
                for group_name, layers in [('low', low_layers), ('mid', mid_layers), ('high', high_layers)]:
                    group_data = layer_result[layer_result['layer'].isin(layers)]
                    if len(group_data) > 0:
                        avg_diff = group_data['weighted_avg_diff'].mean()
                        layer_group_diffs[group_name].append(avg_diff)
                    else:
                        layer_group_diffs[group_name].append(0)
            
            # 3. attention和ffn分组变化
            if layer_groups:
                low_layers, mid_layers, high_layers = layer_groups
                layer_df = df[df['layer_num'] >= 0]
                
                for comp in ['attention', 'ffn']:
                    comp_data = layer_df[layer_df['component'] == comp]
                    for group_name, layers in [('low', low_layers), ('mid', mid_layers), ('high', high_layers)]:
                        group_comp_data = comp_data[comp_data['layer_num'].isin(layers)]
                        if len(group_comp_data) > 0:
                            avg_diff = np.average(group_comp_data['relative_l2_diff'], 
                                                weights=group_comp_data['param_count'])
                            att_ffn_diffs[f'{comp}_{group_name}'].append(avg_diff)
                        else:
                            att_ffn_diffs[f'{comp}_{group_name}'].append(0)
        
        # 计算时序趋势图的统一Y轴尺度
        all_trend_values = []
        all_trend_values.extend(overall_diffs)
        for group_diffs in layer_group_diffs.values():
            all_trend_values.extend(group_diffs)
        for att_ffn_group_diffs in att_ffn_diffs.values():
            all_trend_values.extend(att_ffn_group_diffs)
        
        # 设置统一的Y轴范围（稍微放大一点留出边距）
        trend_y_max = max(all_trend_values) * 1.1 if all_trend_values else 1
        trend_y_min = min(all_trend_values) * 0.9 if min(all_trend_values) > 0 else 0
        
        # 绘制图表
        # 1. 总体参数变化趋势
        axes[0, 0].plot(model_indices, overall_diffs, marker='o', linewidth=2, markersize=6)
        axes[0, 0].set_title('Overall Parameter Change Trend')
        axes[0, 0].set_xlabel('Model Index')
        axes[0, 0].set_ylabel('Weighted Avg Relative L2 Diff')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_ylim(trend_y_min, trend_y_max)
        
        # 2. 层级分组变化趋势
        colors = ['blue', 'green', 'red']
        for i, (group_name, diffs) in enumerate(layer_group_diffs.items()):
            if len(diffs) == len(model_indices):
                axes[0, 1].plot(model_indices, diffs, marker='o', linewidth=2, 
                              markersize=6, label=f'{group_name.capitalize()} Layers', color=colors[i])
        
        axes[0, 1].set_title('Parameter Change by Layer Groups')
        axes[0, 1].set_xlabel('Model Index')
        axes[0, 1].set_ylabel('Weighted Avg Relative L2 Diff')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_ylim(trend_y_min, trend_y_max)
        
        # 3. Attention分组变化趋势
        att_colors = ['lightblue', 'blue', 'darkblue']
        for i, group_name in enumerate(['low', 'mid', 'high']):
            key = f'attention_{group_name}'
            if len(att_ffn_diffs[key]) == len(model_indices):
                axes[1, 0].plot(model_indices, att_ffn_diffs[key], marker='o', linewidth=2,
                              markersize=6, label=f'Attention {group_name.capitalize()}', color=att_colors[i])
        
        axes[1, 0].set_title('Attention Parameter Change by Layer Groups')
        axes[1, 0].set_xlabel('Model Index')
        axes[1, 0].set_ylabel('Weighted Avg Relative L2 Diff')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_ylim(trend_y_min, trend_y_max)
        
        # 4. FFN分组变化趋势
        ffn_colors = ['lightcoral', 'red', 'darkred']
        for i, group_name in enumerate(['low', 'mid', 'high']):
            key = f'ffn_{group_name}'
            if len(att_ffn_diffs[key]) == len(model_indices):
                axes[1, 1].plot(model_indices, att_ffn_diffs[key], marker='o', linewidth=2,
                              markersize=6, label=f'FFN {group_name.capitalize()}', color=ffn_colors[i])
        
        axes[1, 1].set_title('FFN Parameter Change by Layer Groups')
        axes[1, 1].set_xlabel('Model Index')
        axes[1, 1].set_ylabel('Weighted Avg Relative L2 Diff')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_ylim(trend_y_min, trend_y_max)
        
        plt.tight_layout()
        plt.savefig('parameter_change_trends.png', dpi=300, bbox_inches='tight')
        print("时序趋势图已保存为 'parameter_change_trends.png'")
        print(f"时序趋势图使用统一Y轴范围: [{trend_y_min:.6f}, {trend_y_max:.6f}]")
    
    def generate_summary_report(self):
        """生成包含所有模型的综合分析报告"""
        report = []
        report.append("# 多模型参数变化时序分析报告")
        report.append(f"基础模型: {self.path_base}")
        report.append("新模型列表:")
        for i, path in enumerate(self.path_new_list):
            report.append(f"  {i+1}. {path}")
        report.append(f"分析指标: 相对L2差异 (Relative L2 Difference)\n")
        
        # 为每个模型生成统计
        for i, df in enumerate(self.all_results):
            report.append(f"## 模型 {i+1} 统计")
            total_params = df['param_count'].sum()
            avg_diff = np.average(df['relative_l2_diff'], weights=df['param_count'])
            
            report.append(f"总参数量: {total_params:,}")
            report.append(f"加权平均相对L2差异: {avg_diff:.6f}")
            report.append(f"最大相对L2差异: {df['relative_l2_diff'].max():.6f}")
            report.append("")
        
        # 时序变化总结
        if len(self.all_results) > 1:
            overall_diffs = [np.average(df['relative_l2_diff'], weights=df['param_count']) 
                           for df in self.all_results]
            report.append("## 时序变化趋势")
            report.append("各模型整体差异:")
            for i, diff in enumerate(overall_diffs):
                report.append(f"  模型 {i+1}: {diff:.6f}")
            
            if len(overall_diffs) > 1:
                trend = "递增" if overall_diffs[-1] > overall_diffs[0] else "递减"
                report.append(f"总体趋势: {trend}")
                report.append(f"变化幅度: {abs(overall_diffs[-1] - overall_diffs[0]):.6f}")
        
        # 保存报告
        with open('multi_model_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print("综合分析报告已保存为 'multi_model_analysis_report.txt'")
    
    def run_analysis(self):
        """运行完整的多模型时序分析"""
        if not self.load_models():
            return None
        
        print(f"\n开始分析 {len(self.new_models)} 个模型...")
        
        # 分别分析每个模型
        all_layer_results = []
        all_comp_results = []
        all_layer_comp_results = []
        
        for i in range(len(self.new_models)):
            print(f"\n{'='*60}")
            print(f"分析模型 {i+1}/{len(self.new_models)}")
            print(f"{'='*60}")
            
            # 计算差异
            df = self.calculate_relative_l2_diff(i)
            if len(df) == 0:
                print(f"模型 {i+1} 没有参数可分析!")
                continue
            
            self.all_results.append(df)
            
            # 分析组件
            layer_results = self.analyze_layer_differences(df)
            comp_results = self.analyze_component_differences(df)
            layer_comp_results, pivot_table = self.analyze_layer_component_differences(df)
            
            all_layer_results.append(layer_results)
            all_comp_results.append(comp_results)
            all_layer_comp_results.append(layer_comp_results)
            
            # 保存单个模型数据
            df.to_csv(f'parameter_differences_model_{i}.csv', index=False)
            if layer_results is not None:
                layer_results.to_csv(f'layer_differences_model_{i}.csv', index=False)
            comp_results.to_csv(f'component_differences_model_{i}.csv', index=False)
        
        if len(self.all_results) == 0:
            print("没有模型可以分析!")
            return None
        
        # 计算全局尺度
        self.calculate_global_scales()
        
        # 为每个模型创建可视化
        for i, df in enumerate(self.all_results):
            self.create_visualizations(df, all_layer_results[i], all_comp_results[i], 
                                     all_layer_comp_results[i], i)
        
        # 创建统一尺度的时序趋势图
        self.create_trend_visualizations()
        
        # 生成综合报告
        self.generate_summary_report()
        
        print(f"\n{'='*60}")
        print("多模型时序分析完成！关键发现:")
        print(f"{'='*60}")
        
        for i, df in enumerate(self.all_results):
            avg_diff = np.average(df['relative_l2_diff'], weights=df['param_count'])
            print(f"• 模型 {i+1} 整体加权平均相对差异: {avg_diff:.6f}")
        
        if len(self.all_results) > 1:
            overall_diffs = [np.average(df['relative_l2_diff'], weights=df['param_count']) 
                           for df in self.all_results]
            trend = "递增" if overall_diffs[-1] > overall_diffs[0] else "递减"
            print(f"• 整体变化趋势: {trend}")
            print(f"• 变化幅度: {abs(overall_diffs[-1] - overall_diffs[0]):.6f}")
        
        return self.all_results

# 使用示例
if __name__ == "__main__":
    # 修改这里：path_new现在是一个列表
    path_base = "/home/fuzhizhang.fzz/model/DeepSeek-R1-Distill-Qwen-1.5B"
    path_new_list = [
        "/home/fuzhizhang.fzz/model/DeepScaleR-1.5B-Preview"
    ]
    
    analyzer = SimplifiedParameterAnalyzer(path_base, path_new_list)
    results = analyzer.run_analysis()