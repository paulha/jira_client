SELECT
    f.jkey,
    f.summary,
    
    bxtpm.jkey,
    bxtpm.priority,
    bxtpm.status,

    bxtmm.jkey,
    bxtmm.priority,
    bxtmm.status
FROM
    (SELECT * FROM areq_e_features WHERE platform = 'Broxton-P IVI' and version = 'M') as bxtpm
    INNER JOIN areq_features f
        ON (bxtpm.feature_jkey = f.jkey)
    LEFT OUTER JOIN (
        SELECT * from areq_e_features WHERE platform = 'Broxton' AND version = 'M') AS bxtmm
    ON (bxtpm.feature_jkey = bxtmm.feature_jkey)
WHERE
    bxtpm.priority like 'P1%'
    AND bxtpm.rejected = 0
    AND (IFNULL(bxtmm.rejected,1) = 1 OR IFNULL(bxtmm.priority, bxtpm.priority) != bxtpm.priority)

ORDER BY
	f.summary
;
