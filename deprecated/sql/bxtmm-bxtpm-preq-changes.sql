SELECT
    bxtmm.global_id,
    bxtmm.jkey,
    bxtmm.summary,
    bxtmm.priority,
    bxtmm.status,
    
    bxtpm.jkey,
    bxtpm.priority,
    bxtpm.status
FROM
    (SELECT * FROM preq_features WHERE platform = 'Broxton' AND version = 'M') AS bxtmm
    LEFT OUTER JOIN
        (SELECT * FROM preq_features WHERE platform = 'Broxton-P IVI' and version = 'M') AS bxtpm
    ON (bxtmm.global_id = bxtpm.global_id)
WHERE
    bxtmm.priority like 'P1%'
    AND bxtmm.rejected = 0
    AND (IFNULL(bxtpm.rejected,1) = 1 OR IFNULL(bxtpm.priority, bxtmm.priority) != bxtmm.priority)
ORDER BY bxtmm.summary
;
