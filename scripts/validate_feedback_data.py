#!/usr/bin/env python3
"""
验证 feedback 数据的完整性
检查是否有不符合标准格式的数据
"""
import sqlite3
import json
from datetime import datetime

# 标准的 feedback 类型
VALID_FEEDBACK_TYPES = {'resonance', 'rejection', 'ignore'}

# 标准的 behavior 类型
VALID_BEHAVIORS = {'agree', 'download', 'explain', 'comment', 'timeout'}

def validate_feedback_data(db_path='data/zenai.db'):
    """验证 feedback 数据"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("ZenAi Feedback 数据验证")
    print("=" * 70)
    
    # 1. 检查总记录数
    cursor.execute("SELECT COUNT(*) FROM interactions")
    total_count = cursor.fetchone()[0]
    print(f"\n总记录数: {total_count}")
    
    # 2. 检查 feedback 字段
    print("\n" + "=" * 70)
    print("1. 验证 feedback 字段")
    print("=" * 70)
    
    cursor.execute("""
        SELECT feedback, COUNT(*) as count
        FROM interactions
        GROUP BY feedback
    """)
    
    invalid_feedback = []
    for row in cursor.fetchall():
        feedback, count = row
        if feedback in VALID_FEEDBACK_TYPES:
            print(f"✅ {feedback}: {count} 条记录")
        else:
            print(f"⚠️  {feedback}: {count} 条记录 (非标准类型)")
            invalid_feedback.append((feedback, count))
    
    # 3. 检查 extra_data 字段
    print("\n" + "=" * 70)
    print("2. 验证 extra_data 字段")
    print("=" * 70)
    
    cursor.execute("SELECT id, extra_data FROM interactions")
    
    empty_count = 0
    with_behavior = 0
    with_comment = 0
    invalid_json = []
    invalid_behavior = []
    
    for row in cursor.fetchall():
        interaction_id, extra_data_json = row
        
        try:
            extra_data = json.loads(extra_data_json) if extra_data_json else {}
            
            # 统计
            if not extra_data or extra_data == {}:
                empty_count += 1
            
            if 'behavior' in extra_data:
                with_behavior += 1
                # 验证 behavior 值
                if extra_data['behavior'] not in VALID_BEHAVIORS:
                    invalid_behavior.append((interaction_id, extra_data['behavior']))
            
            if 'comment' in extra_data:
                with_comment += 1
                
        except json.JSONDecodeError:
            invalid_json.append(interaction_id)
    
    print(f"空 extra_data: {empty_count} 条 (旧数据，正常)")
    print(f"包含 behavior: {with_behavior} 条 (新数据)")
    print(f"包含 comment: {with_comment} 条 (有评论/解释)")
    
    if invalid_json:
        print(f"\n⚠️  JSON 解析错误: {len(invalid_json)} 条")
        print(f"   IDs: {invalid_json[:5]}...")
    else:
        print(f"\n✅ 所有 JSON 数据格式正确")
    
    if invalid_behavior:
        print(f"\n⚠️  非标准 behavior: {len(invalid_behavior)} 条")
        for interaction_id, behavior in invalid_behavior[:5]:
            print(f"   ID {interaction_id}: '{behavior}'")
    else:
        print(f"✅ 所有 behavior 类型正确")
    
    # 4. 数据完整性检查
    print("\n" + "=" * 70)
    print("3. 数据完整性检查")
    print("=" * 70)
    
    # 检查是否有 feedback 和 behavior 不匹配的情况
    cursor.execute("""
        SELECT 
            id,
            feedback,
            json_extract(extra_data, '$.behavior') as behavior
        FROM interactions
        WHERE json_extract(extra_data, '$.behavior') IS NOT NULL
    """)
    
    mismatches = []
    expected_mapping = {
        'agree': 'resonance',
        'download': 'resonance',
        'explain': 'rejection',
        'comment': 'ignore',
        'timeout': 'ignore'
    }
    
    for row in cursor.fetchall():
        interaction_id, feedback, behavior = row
        expected = expected_mapping.get(behavior)
        if expected and feedback != expected:
            mismatches.append((interaction_id, behavior, feedback, expected))
    
    if mismatches:
        print(f"⚠️  映射不匹配: {len(mismatches)} 条")
        for interaction_id, behavior, actual, expected in mismatches[:5]:
            print(f"   ID {interaction_id}: behavior='{behavior}' → "
                  f"feedback='{actual}' (应为 '{expected}')")
    else:
        print(f"✅ 所有 behavior→feedback 映射正确")
    
    # 5. 总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    issues = []
    if invalid_feedback:
        issues.append(f"非标准 feedback 类型: {len(invalid_feedback)} 种")
    if invalid_json:
        issues.append(f"JSON 格式错误: {len(invalid_json)} 条")
    if invalid_behavior:
        issues.append(f"非标准 behavior: {len(invalid_behavior)} 条")
    if mismatches:
        issues.append(f"映射不匹配: {len(mismatches)} 条")
    
    if issues:
        print("\n⚠️  发现以下问题:")
        for issue in issues:
            print(f"   - {issue}")
        print("\n建议运行修复脚本进行数据清理")
    else:
        print("\n🎉 数据验证通过！所有数据格式正确。")
        print("\n数据分布:")
        print(f"   - 旧数据（无 behavior）: {empty_count} 条")
        print(f"   - 新数据（有 behavior）: {with_behavior} 条")
        print(f"   - 包含评论/解释: {with_comment} 条")
    
    conn.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    validate_feedback_data()
