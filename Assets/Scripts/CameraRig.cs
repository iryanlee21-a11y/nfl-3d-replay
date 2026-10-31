using UnityEngine;

/// <summary>
/// 선수 시점 카메라. 선수 머리 높이에서 달리는 방향을 바라본다.
/// 자식에 Camera가 있어야 한다.
/// </summary>
public class CameraRig : MonoBehaviour
{
    public float eyeHeight = 2.0f;          // 야드 (약 1.8m)
    public float turnSmoothing = 6f;
    Vector3 lookDir = Vector3.right;        // 기본: 공격 방향

    public void Follow(Transform player, Vector3 velocity)
    {
        transform.position = player.position + Vector3.up * eyeHeight;
        Vector3 flat = new Vector3(velocity.x, 0f, velocity.z);
        if (flat.sqrMagnitude > 1e-4f) lookDir = Vector3.Slerp(lookDir, flat.normalized, Time.deltaTime * turnSmoothing);
        transform.rotation = Quaternion.LookRotation(lookDir, Vector3.up);
    }
}
