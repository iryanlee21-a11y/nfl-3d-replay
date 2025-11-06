using UnityEngine;

public class PlayerController : MonoBehaviour
{
    [Header("Player Identity")]
    public int playerId = 0;
    public string playerRole = "QB"; // 예: QB, RB, WR 등

    [Header("Head Transform (camera attach)")]
    public Transform headTransform;

    // (디버그용) 현재 위치 업데이트 함수
    public void SetPosition(Vector3 worldPos)
    {
        transform.position = worldPos;
    }

    // (디버그) 머리 위치 반환
    public Vector3 HeadPosition()
    {
        if (headTransform != null) return headTransform.position;
        return transform.position + Vector3.up * 1.0f;
    }
}
