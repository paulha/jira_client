SELECT
    f.jkey,
    f.summary,
    
    bxtpn.jkey,
    bxtpn.priority,
    bxtpn.status,

    bxtpm.jkey,
    bxtpm.priority,
    bxtpm.status
FROM
    (SELECT * FROM areq_e_features WHERE platform = 'Broxton-P IVI' and version in ('N', 'O')) as bxtpn
    INNER JOIN areq_features f
        ON (bxtpn.feature_jkey = f.jkey)
    LEFT OUTER JOIN (
        SELECT * from areq_e_features WHERE platform = 'Broxton-P IVI' AND version = 'M') AS bxtpm
    ON (bxtpn.feature_jkey = bxtpm.feature_jkey)
WHERE
    bxtpn.priority like 'P1%'
    AND bxtpn.rejected = 0
    AND (IFNULL(bxtpm.rejected,1) = 1 OR IFNULL(bxtpm.priority, bxtpn.priority) != bxtpn.priority)

ORDER BY
	f.summary
;
