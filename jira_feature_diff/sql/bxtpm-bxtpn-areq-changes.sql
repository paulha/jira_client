SELECT
    f.jkey,
    f.summary,
    
    bxtpm.jkey,
    bxtpm.priority,
    bxtpm.status,

    bxtpn.jkey,
    bxtpn.priority,
    bxtpn.status
FROM
    (SELECT * FROM areq_e_features WHERE platform = 'Broxton-P IVI' and version = 'M') as bxtpm
    INNER JOIN areq_features f
        ON (bxtpm.feature_jkey = f.jkey)
    LEFT OUTER JOIN (
        SELECT * from areq_e_features WHERE platform = 'Broxton-P IVI' AND version IN ('N', 'O')) AS bxtpn
    ON (bxtpm.feature_jkey = bxtpn.feature_jkey)
WHERE
    bxtpm.priority like 'P1%'
    AND bxtpm.rejected = 0
    AND (IFNULL(bxtpn.rejected,1) = 1 OR IFNULL(bxtpn.priority, bxtpm.priority) != bxtpm.priority)

ORDER BY
	f.summary
;
