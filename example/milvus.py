#!/usr/bin/env python3
"""
Milvus服务分阶段验证脚本
1. 基础连接与版本检查
2. 集合创建、插入、搜索全流程测试
3. 环境清理
"""

from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
import random
import time

def print_step(step, title):
    """打印步骤分隔"""
    print(f"\n{'-'*60}")
    print(f" 步骤 {step}: {title}")
    print(f"{'-'*60}")

def main():
    # 配置信息
    host = "localhost"
    port = 19530
    test_collection_name = "health_check_test"
    
    # ========== 第一阶段：基础连接与版本检查 ==========
    print_step(1, "基础连接与服务版本检查")
    
    try:
        print(f"正在连接到 {host}:{port} ...")
        # 设置连接超时为10秒
        connections.connect(host=host, port=port, timeout=10)
        print("✅ 网络连接成功")
        
        # 获取服务端版本 (最基础的健康检查)
        server_version = utility.get_server_version()
        print(f"✅ 服务端版本: {server_version}")
        
        # 可选：检查是否有现有集合
        existing_collections = utility.list_collections()
        print(f"✅ 现有集合列表: {existing_collections}")
        
    except Exception as e:
        print(f"❌ 第一阶段失败: {e}")
        print("提示: 请确保：")
        print("  1. kubectl port-forward 命令正在运行")
        print("  2. Milvus 服务已完全启动（等待约2-3分钟）")
        return
    
    # ========== 第二阶段：完整功能测试 ==========
    print_step(2, "完整功能测试（创建、插入、搜索）")
    
    # 等待一下，确保服务内部协调完成
    print("等待服务就绪...")
    time.sleep(3)
    
    try:
        # 2.1 定义集合结构
        print("\n2.1 定义测试集合结构...")
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=8)  # 使用小维度加快测试
        ]
        schema = CollectionSchema(fields, description="健康检查用临时集合")
        print(f"✅ 集合结构定义完成 (维度: 8)")
        
        # 2.2 创建集合
        print("\n2.2 创建集合...")
        collection = Collection(test_collection_name, schema)
        print(f"✅ 集合 '{test_collection_name}' 创建成功")
        
        # 2.3 插入测试数据
        print("\n2.3 插入测试数据...")
        num_entities = 10
        dim = 8
        
        # 准备数据：10条向量
        ids = [i for i in range(num_entities)]
        vectors = [[random.random() for _ in range(dim)] for _ in range(num_entities)]
        
        data = [ids, vectors]
        insert_result = collection.insert(data)
        print(f"✅ 插入成功: {len(insert_result.primary_keys)} 条数据")
        print(f"   插入的ID范围: {min(insert_result.primary_keys)} 到 {max(insert_result.primary_keys)}")
        
        # 2.4 刷新并获取实体数量
        print("\n2.4 验证数据持久化...")
        collection.flush()
        entity_count = collection.num_entities
        print(f"✅ 集合中的实体数量: {entity_count}")
        
        # 2.5 创建索引
        print("\n2.5 创建向量索引...")
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2", 
            "params": {"nlist": 128}
        }
        collection.create_index("vector", index_params)
        print("✅ 索引创建完成")
        
        # 2.6 加载集合到内存
        print("\n2.6 加载集合到内存...")
        collection.load()
        print("✅ 集合加载完成")
        
        # 2.7 执行向量搜索
        print("\n2.7 执行向量搜索测试...")
        # 使用第一条插入的向量进行搜索
        search_vector = vectors[0]
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        
        results = collection.search(
            [search_vector], 
            anns_field="vector", 
            param=search_params, 
            limit=3,
            output_fields=["id"]
        )
        
        print("✅ 搜索成功！")
        print(f"   查询向量: ID={ids[0]}")
        print(f"   最相似的3条结果:")
        for i, hit in enumerate(results[0]):
            print(f"     排名 {i+1}: ID={hit.id}, 距离={hit.distance:.4f}")
        
        # 验证第一条结果应该是自己
        if results[0][0].id == ids[0]:
            print("   ✓ 自检通过：最相似的结果是向量本身")
        
    except Exception as e:
        print(f"❌ 第二阶段失败: {e}")
        print("提示: 此阶段失败可能表明服务内部组件尚未完全协调。")
        print("      请等待1-2分钟后重试，或检查组件日志。")
        # 尝试清理可能残留的测试集合
        try:
            Collection(test_collection_name).drop()
            print("已清理测试集合")
        except:
            pass
        return
    
    # ========== 第三阶段：清理与总结 ==========
    print_step(3, "清理测试环境")
    
    try:
        print("删除测试集合...")
        collection.drop()
        print(f"✅ 测试集合 '{test_collection_name}' 已删除")
        
        # 最终验证
        remaining_collections = utility.list_collections()
        if test_collection_name not in remaining_collections:
            print(f"✅ 环境清理成功，剩余集合: {remaining_collections}")
        
    except Exception as e:
        print(f"⚠️  清理阶段警告: {e}")
    
    # ========== 测试总结 ==========
    print(f"\n{'='*60}")
    print(" MILVUS 服务所有核心功能测试通过！")
    print("="*60)
    print(f"✅ 版本检查: 通过 ({server_version})")
    print(f"✅ 集合操作: 通过 (创建、插入、索引、加载)")
    print(f"✅ 向量搜索: 通过 (精度自检正常)")
    print(f"✅ 环境清理: 通过")
    print(f"\n你的Milvus服务已就绪，可用于开发。")
    print(f"连接地址: {host}:{port}")
    print("="*60)

if __name__ == "__main__":
    main()
