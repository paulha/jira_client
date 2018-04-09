SELECT
    bxtpm.global_id,
    bxtpm.jkey,
    bxtpm.summary,
    bxtpm.priority,
    bxtpm.status,
    
    bxtpn.jkey,
    bxtpn.priority,
    bxtpn.status
FROM
    (SELECT * FROM preq_features WHERE platform = 'Broxton-P IVI' AND version = 'M') AS bxtpm
    LEFT OUTER JOIN
        (SELECT * FROM preq_features WHERE platform = 'Broxton-P IVI' AND version IN ('N', 'O')) AS bxtpn
    ON (bxtpm.global_id = bxtpn.global_id)
WHERE
    bxtpm.priority like 'P1%'
    AND bxtpm.rejected = 0
    AND (IFNULL(bxtpn.rejected,1) = 1 OR IFNULL(bxtpn.priority, bxtpm.priority) != bxtpm.priority)
ORDER BY bxtpm.summary


;
