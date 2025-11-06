using UnityEngine;

public class CameraRig : MonoBehaviour
{
    [Header("Assign the player whose POV this camera will follow")]
    public PlayerController targetPlayer;

    [Header("Camera offset from head (local)")]
    public Vector3 localOffset = Vector3.zero;

    private Camera cam;

    void Awake()
    {
        cam = GetComponentInChildren<Camera>();
        if (cam == null)
        {
            Debug.LogWarning("No Camera found under CameraRig. Add a Camera as a child.");
        }
    }

    void LateUpdate()
    {
        if (targetPlayer != null && cam != null)
        {
            Transform head = targetPlayer.headTransform;
            if (head != null)
            {
                // 머리 위치에 오프셋 적용
                transform.position = head.position + head.TransformVector(localOffset);
                transform.rotation = head.rotation;
            }
            else
            {
                transform.position = targetPlayer.transform.position + Vector3.up * 1.0f;
            }
        }
    }
}