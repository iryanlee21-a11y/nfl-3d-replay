using UnityEngine;

public class PlayerMarker : MonoBehaviour
{
    public int Id;
    public TrailRenderer Trail;
    public float SmoothTime = 0.05f;

    private Vector3 _velocity = Vector3.zero;

    public void Initialize(int id, Color color)
    {
        Id = id;

        if (Trail != null)
        {
            Trail.startColor = color;
            Trail.endColor = color;
        }
    }

    public void MoveTo(Vector3 target)
    {
        transform.position = Vector3.SmoothDamp(
            transform.position,
            target,
            ref _velocity,
            SmoothTime
        );
    }
}