SELECT
    bxtpn.global_id,
    bxtpn.jkey,
    bxtpn.summary,
    bxtpn.priority,
    bxtpn.status,
    
    bxtpm.jkey,
    bxtpm.priority,
    bxtpm.status
FROM
    (SELECT * FROM preq_features WHERE platform = 'Broxton-P IVI' AND version IN ('N', 'O')) AS bxtpn
    LEFT OUTER JOIN
        (SELECT * FROM preq_features WHERE platform = 'Broxton-P IVI' AND version = 'M') AS bxtpm
    ON (bxtpn.global_id = bxtpm.global_id)
WHERE
    bxtpn.priority like 'P1%'
    AND bxtpn.rejected = 0
    AND (IFNULL(bxtpm.rejected,1) = 1 OR IFNULL(bxtpm.priority, bxtpn.priority) != bxtpn.priority)
ORDER BY bxtpn.summary
;
