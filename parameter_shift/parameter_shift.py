import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoModel
from collections import defaultdict

class SimplifiedParameterAnalyzer:
    def __init__(self, path_base, path_new):
        self.path_base = path_base
        self.path_new = path_new
        self.base_model = None
        self.new_model = None
        
    def load_models(self):
        """加载模型"""
        print("Loading models...")
        try:
            self.base_model = AutoModel.from_pretrained(
                self.path_base, torch_dtype=torch.float32, trust_remote_code=True
            )
            self.new_model = AutoModel.from_pretrained(
                self.path_new, torch_dtype=torch.float32, trust_remote_code=True
            )
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
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
    
    def calculate_relative_l2_diff(self):
        """计算所有参数的相对L2差异"""
        base_params = dict(self.base_model.named_parameters())
        new_params = dict(self.new_model.named_parameters())
        
        common_keys = set(base_params.keys()) & set(new_params.keys())
        print(f"Analyzing {len(common_keys)} common parameters...")
        
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
                    'relative_l2_diff': relative_l2
                })
        
        return pd.DataFrame(results)
    
    def analyze_layer_differences(self, df):
        """分析每一层的参数差异"""
        print("\n" + "="*60)
        print("每一层参数差异分析")
        print("="*60)
        
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
        print("\n" + "="*60)
        print("各组件整体差异分析")
        print("="*60)
        
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
        print("\n" + "="*60)
        print("每一层attention和ffn差异分析")
        print("="*60)
        
        # 只分析有层号的attention和ffn
        layer_df = df[df['layer_num'] >= 0]
        target_components = ['attention', 'ffn']
        layer_df = layer_df[layer_df['component'].isin(target_components)]
        
        if len(layer_df) == 0:
            print("未找到层级attention/ffn信息")
            return None
        
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
        att_total = layer_comp_results[layer_comp_results['component'] == 'attention']['weighted_avg_diff'].mean()
        ffn_total = layer_comp_results[layer_comp_results['component'] == 'ffn']['weighted_avg_diff'].mean()
        
        print(f"\n整体对比:")
        print(f"Attention平均差异: {att_total:.6f}")
        print(f"FFN平均差异: {ffn_total:.6f}")
        print(f"FFN/Attention差异比例: {ffn_total/att_total:.3f}" if att_total > 0 else "")
        
        return layer_comp_results, pivot_table
    
    def create_visualizations(self, df, layer_results, comp_results, layer_comp_results):
        """创建简化的可视化图表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 各层差异
        if layer_results is not None:
            axes[0, 0].bar(layer_results['layer'], layer_results['weighted_avg_diff'])
            axes[0, 0].set_title('Parameter Differences by Layer')
            axes[0, 0].set_xlabel('Layer Number')
            axes[0, 0].set_ylabel('Weighted Avg Relative L2 Diff')
        
        # 2. 各组件差异
        axes[0, 1].bar(comp_results['component'], comp_results['weighted_avg_diff'])
        axes[0, 1].set_title('Parameter Differences by Component')
        axes[0, 1].set_xlabel('Component')
        axes[0, 1].set_ylabel('Weighted Avg Relative L2 Diff')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 各层attention vs ffn
        if layer_comp_results is not None:
            att_data = layer_comp_results[layer_comp_results['component'] == 'attention']
            ffn_data = layer_comp_results[layer_comp_results['component'] == 'ffn']
            
            x = att_data['layer']
            width = 0.35
            
            axes[1, 0].bar(x - width/2, att_data['weighted_avg_diff'], width, label='Attention')
            axes[1, 0].bar(x + width/2, ffn_data['weighted_avg_diff'], width, label='FFN')
            axes[1, 0].set_title('Attention vs FFN by Layer')
            axes[1, 0].set_xlabel('Layer Number')
            axes[1, 0].set_ylabel('Weighted Avg Relative L2 Diff')
            axes[1, 0].legend()
        
        # 4. 参数变化分布
        axes[1, 1].hist(df['relative_l2_diff'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        axes[1, 1].set_title('Distribution of Relative L2 Differences')
        axes[1, 1].set_xlabel('Relative L2 Difference')
        axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig('simplified_parameter_analysis.png', dpi=300, bbox_inches='tight')
        print("\n可视化图表已保存为 'simplified_parameter_analysis.png'")
    
    def generate_summary_report(self, df, layer_results, comp_results):
        """生成简洁的分析报告"""
        report = []
        report.append("# 模型参数变化分析报告")
        report.append(f"基础模型: {self.path_base}")
        report.append(f"新模型: {self.path_new}")
        report.append(f"分析指标: 相对L2差异 (Relative L2 Difference)\n")
        
        # 总体统计
        total_params = df['param_count'].sum()
        avg_diff = np.average(df['relative_l2_diff'], weights=df['param_count'])
        
        report.append("## 总体统计")
        report.append(f"总参数量: {total_params:,}")
        report.append(f"加权平均相对L2差异: {avg_diff:.6f}")
        report.append(f"最大相对L2差异: {df['relative_l2_diff'].max():.6f}\n")
        
        # 组件统计
        report.append("## 各组件差异统计")
        report.append(comp_results.to_string(index=False, float_format='%.6f'))
        report.append("")
        
        # 层级统计（如果有）
        if layer_results is not None:
            report.append("## 各层差异统计")
            report.append(layer_results.to_string(index=False, float_format='%.6f'))
        
        # 保存报告
        with open('simplified_analysis_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print("分析报告已保存为 'simplified_analysis_report.txt'")
    
    def run_analysis(self):
        """运行完整的简化分析"""
        if not self.load_models():
            return None
        
        # 计算相对L2差异
        df = self.calculate_relative_l2_diff()
        
        if len(df) == 0:
            print("没有参数可分析!")
            return None
        
        # 三个核心分析
        layer_results = self.analyze_layer_differences(df)
        comp_results = self.analyze_component_differences(df)
        layer_comp_results, pivot_table = self.analyze_layer_component_differences(df)
        
        # 创建可视化
        self.create_visualizations(df, layer_results, comp_results, layer_comp_results)
        
        # 生成报告
        self.generate_summary_report(df, layer_results, comp_results)
        
        # 保存核心数据
        df.to_csv('parameter_differences_simple.csv', index=False)
        if layer_results is not None:
            layer_results.to_csv('layer_differences.csv', index=False)
        comp_results.to_csv('component_differences.csv', index=False)
        
        print("\n" + "="*50)
        print("分析完成！关键发现:")
        print("="*50)
        avg_diff = np.average(df['relative_l2_diff'], weights=df['param_count'])
        print(f"• 整体加权平均相对差异: {avg_diff:.6f}")
        
        if len(comp_results) > 0:
            max_comp = comp_results.iloc[0]
            print(f"• 变化最大的组件: {max_comp['component']} (差异: {max_comp['weighted_avg_diff']:.6f})")
        
        if layer_results is not None and len(layer_results) > 0:
            max_layer = layer_results.loc[layer_results['weighted_avg_diff'].idxmax()]
            print(f"• 变化最大的层: Layer {max_layer['layer']} (差异: {max_layer['weighted_avg_diff']:.6f})")
        
        return df

# 使用示例
if __name__ == "__main__":
    path_base = "/home/fuzhizhang.fzz/model/Qwen2.5-3B"
    path_new = "/home/fuzhizhang.fzz/open-r1/data/Qwen2.5-3B-GRPO/checkpoint-2000"
    
    analyzer = SimplifiedParameterAnalyzer(path_base, path_new)
    results = analyzer.run_analysis()